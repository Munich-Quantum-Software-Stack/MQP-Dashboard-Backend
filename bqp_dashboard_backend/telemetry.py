import json
import os
import gzip
import time

from flask import Blueprint, stream_with_context, request, Response
from flask_jwt_extended import jwt_required
from http import HTTPStatus
from eliot import log_call

import influxdb
from influxdb import InfluxDBClient

BLUEPRINT = Blueprint("telemetry", __name__)

# Define constants
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CHUNK_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
EXPIRY_TIME = 3600  # seconds
DELAY_TIME = 60  # seconds
SENSOR_CACHE_TTL = 300  # seconds
SENSOR_MAP_CACHE = {"data": [], "timestamp": 0}


class TelemetryError(Exception):
    """Telemetry module-specific exception."""


# Open connection to InfluxDB
def _open_influxdb():
    try:
        client = InfluxDBClient(
            host=os.getenv("PROXY_DB_HOST"),
            port=os.getenv("PROXY_DB_PORT"),
            database=os.getenv("PROXY_DB"),
            username=os.getenv("PROXY_DB_USER"),
            password=os.getenv("PROXY_DB_PASS"),
        )
        return client
    except TypeError as err:
        raise TelemetryError(str(err)) from err


# -------------------------------------------------------------------
# API: get_available_sensors
# Desc: Request to get available sensors of each measurement, refresh every SENSOR_CACHE_TTL seconds
# Return: sensors list
# -------------------------------------------------------------------
@BLUEPRINT.get("/telemetry/sensors")
@jwt_required()
@log_call
def get_available_sensors():
    """
    API to get all available sensors, refresh every SENSOR_CACHE_TTL seconds

    Returns:
        dict: sensor list
    """
    global SENSOR_MAP_CACHE
    now = time.time()

    if SENSOR_MAP_CACHE["data"] is None or (
        now - SENSOR_MAP_CACHE["timestamp"] > SENSOR_CACHE_TTL
    ):
        try:
            SENSOR_MAP_CACHE["data"] = build_sensor_map()
        except TelemetryError as error:
            return {"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR
        SENSOR_MAP_CACHE["timestamp"] = now

    return SENSOR_MAP_CACHE["data"]


# Internal API: get_measurements
def get_measurements(client):
    return client.get_list_measurements()


# Internal API: get_sensors_from_measurement()
def get_sensors_from_measurement(client, measurement):
    return client.query(f"SHOW FIELD KEYS FROM {measurement}")


# Internal API: build_sensor_map
def build_sensor_map():
    """
    SENSOR_MAP = [
        {
            "measurement": "measurement_name",
            "sensors": []
        },
        ...
    ]
    """
    sensor_map = []  # list()
    try:
        client = _open_influxdb()
        measurements_list = get_measurements(client)
        for item in measurements_list:
            measurement_name = item.get("name")
            sensors = get_sensors_from_measurement(client, measurement_name)
            measurement_sensors = []
            for sensor in sensors.get_points():
                measurement_sensors.append(sensor.get("fieldKey"))
            sensor_map.append(
                {"measurement": measurement_name, "sensors": measurement_sensors}
            )
        client.close()
        return sensor_map
    except TypeError as error:
        return {"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR


# -------------------------------------------------------------------
# API: get_telemetry_data
# args: user's input
# Desc: Request to get Telemetry data
# Return: list of data sources
# -------------------------------------------------------------------
@BLUEPRINT.post("/telemetry")
@jwt_required()
@log_call
def get_telemetry_data():
    """
    API to get telemetry data accordings to user's input.
    Temporary save data to a file on /uploads folder

    Args:
        measurements (list): requested measurements
        sensors (list): requested sensors
        from_timestamp (integer): start time of time window
        to_timestamp (integer): end time of time window
        group_by (string): group by value of user

    Returns:
        file_size (integer): size of saved file
        file_name (string): name of saved file
    """
    data = request.get_json()
    measurements = data.get("measurements", [])
    sensors = data.get("sensors", [])
    from_timestamp = data.get("from_timestamp")
    to_timestamp = data.get("to_timestamp")
    request_interval = data.get("group_by")

    client = _open_influxdb()
    if not measurements:
        measurements = get_measurements(client)

    # Get matched request sensors with available sensors
    matched_sensors = []
    available_sensors = get_available_sensors()
    if not sensors:
        matched_sensors = available_sensors
    else:
        matched_sensors = build_matched_sensors(sensors, available_sensors)

    # Get interval by user
    interval = request_interval
    # Otherwise get default interval by timestamps
    if interval is None or len(interval) == 0:
        interval = get_default_interval(from_timestamp, to_timestamp)

    telemetry_data = {}

    for measurement in matched_sensors:
        measurement_name = measurement.get("measurement")
        sensors = measurement.get("sensors")
        # for sensor in sensors:
        #     query = 'SELECT mean("' + sensor + '") FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms GROUP BY time(' + interval + ') fill(null) ORDER BY time ASC'
        #     query_result = client.query(query)
        query = build_telemetry_query(measurement_name, sensors, from_timestamp, to_timestamp, interval)

        if not query:
            continue
        query_result = client.query(query)
        if len(query_result) > 0:                
            points = []
            for series in query_result.raw.get("series", []):
                columns = series["columns"]
                for row in series["values"]:
                    record = dict(zip(columns, row))
                    points.append(record)
            telemetry_data[measurement_name] = points
    client.close()
    if len(telemetry_data) == 0:
        telemetry_data = "No data."

    # Save data to file
    filename = f"{int(time.time())}_telemetry.json.gz"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file_path = create_compressed_file(telemetry_data, file_path)
    filesize = os.path.getsize(file_path)
    return {"filesize": filesize, "filename": filename}, HTTPStatus.OK


# Internal API: get_interval
def get_default_interval(start, end):
    duration = (end - start) / 1000
    if duration > (7 * 24 * 3600):
        return "1h"
    elif duration > (24 * 3600):
        return "5m"
    else:
        return "1m"


# Internal API: build_telemetry_query
def build_telemetry_query(measurement, sensors, start, end, interval):
    if sensors is None:
        return None

    # for sensor in sensors:
    #     query = 'SELECT mean("' + sensor + '") FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms GROUP BY time(' + group_by + ') fill(null) ORDER BY time ASC'

    sensor_expr = ", ".join([f'mean("{sensor}")' for sensor in sensors])
    query = f"""
    SELECT {sensor_expr}
    FROM "{measurement}"
    WHERE time >= {str(start)}ms AND time <= {str(end)}ms
    GROUP BY time({interval}) fill(null) ORDER BY time ASC
    """
    return query


# Internal API: match_sensors
def build_matched_sensors(sensors, available_sensors):
    result = []

    sensor_set = set(sensors)
    for item in available_sensors:
        matched = [s for s in item.get("sensors") if s in sensor_set]
        if matched:
            result.append({"measurement": item.get("measurement"), "sensors": matched})

    return result


# Internal API: write_data
def create_compressed_file(data, output_path):
    # write compressed data
    # compressed_data = str.encode((json.dumps(data)))
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return output_path


# -------------------------------------------------------------------
# API: download_telemetry_file
# args: filename
# Desc: Sending telemetry file and delete it after downloading
# Return: File
# -------------------------------------------------------------------
@BLUEPRINT.get("/telemetry/download")
def download_telemetry_file():
    """
    Sending file and deleting it after finishing process

    Args:
        string: filename

    Returns:
        File: File object that matches given name
    """
    filename = request.args.get("filename")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return {"error": "File not found"}, HTTPStatus.NOT_FOUND

    def generate():
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_FILE_SIZE):
                    yield chunk
        finally:
            os.remove(file_path)

    return Response(
        stream_with_context(generate()),
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/gzip",
        },
    )
