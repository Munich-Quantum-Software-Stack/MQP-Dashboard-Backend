# ------------------------------------------------------------------------------
# Copyright 2026 Munich Quantum Software Stack Project
#
# Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://github.com/Munich-Quantum-Software-Stack/QDMI/blob/develop/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# ------------------------------------------------------------------------------

"""MQP Dashboard Telemetry Module"""

import json
import os
import gzip
import time
from http import HTTPStatus

from flask import Blueprint, stream_with_context, request, Response
from flask_jwt_extended import jwt_required
from eliot import log_call
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
        db_client = InfluxDBClient(
            host=os.getenv("PROXY_DB_HOST"),
            port=os.getenv("PROXY_DB_PORT"),
            database=os.getenv("PROXY_DB"),
            username=os.getenv("PROXY_DB_USER"),
            password=os.getenv("PROXY_DB_PASS"),
        )
        return db_client
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
def get_available_sensors() -> list[dict]:
    """
    API to get all available sensors, refresh every SENSOR_CACHE_TTL seconds

    Returns:
        dict: sensor list
    """
    # global SENSOR_MAP_CACHE
    now = time.time()

    if SENSOR_MAP_CACHE["data"] is None or (
        now - SENSOR_MAP_CACHE["timestamp"] > SENSOR_CACHE_TTL
    ):
        try:
            SENSOR_MAP_CACHE["data"] = _build_sensor_map()
        except TelemetryError as error:
            return {"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR
        SENSOR_MAP_CACHE["timestamp"] = now

    return SENSOR_MAP_CACHE["data"]


# Internal API: get_measurements
def _get_measurements(db_client):
    return db_client.get_list_measurements()


# Internal API: _get_sensors_from_measurement()
def _get_sensors_from_measurement(db_client, measurement):
    return db_client.query(f"SHOW FIELD KEYS FROM {measurement}")


# Internal API: _build_sensor_map
def _build_sensor_map():
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
        db_client = _open_influxdb()
        measurements_list = _get_measurements(db_client)
        for item in measurements_list:
            measurement_name = item.get("name")
            sensors = _get_sensors_from_measurement(db_client, measurement_name)
            measurement_sensors = []
            for sensor in sensors.get_points():
                measurement_sensors.append(sensor.get("fieldKey"))
            sensor_map.append(
                {"measurement": measurement_name, "sensors": measurement_sensors}
            )
        db_client.close()
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
def get_telemetry_data() -> tuple[dict, HTTPStatus]:
    """
    API to get telemetry data accordings to user's input.
    Temporary save data to a file on /uploads folder

    Query parameters:
        - measurements (list): requested measurements
        - sensors (list): requested sensors
        - from_timestamp (integer): start time of time window
        - to_timestamp (integer): end time of time window
        - group_by (string): group by value of user

    Returns:
        file_size (integer): size of saved file
        file_name (string): name of saved file
    """
    measurements, sensors, from_timestamp, to_timestamp, request_interval = (
        _parse_telemetry_request()
    )

    db_client = _open_influxdb()
    if not measurements:
        measurements = _get_measurements(db_client)

    # Get matched request sensors with available sensors
    matched_sensors = _resolve_sensors(sensors)

    # Get interval
    interval = _resolve_interval(request_interval, from_timestamp, to_timestamp)

    # Fetch telemetry data
    telemetry_data = _fetch_telemetry(
        db_client, matched_sensors, from_timestamp, to_timestamp, interval
    )
    db_client.close()

    if not telemetry_data:
        return {"filesize": 0, "filename": ""}, HTTPStatus.OK

    # Save data to file
    filename = f"{int(time.time())}_telemetry.json.gz"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file_path = _create_compressed_file(telemetry_data, file_path)
    filesize = os.path.getsize(file_path)
    return {"filesize": filesize, "filename": filename}, HTTPStatus.OK


# Internal API: _parse_telemetry_request
def _parse_telemetry_request():
    data = request.get_json()
    measurements = data.get("measurements", [])
    sensors = data.get("sensors", [])
    from_timestamp = int(data.get("from_timestamp"))
    to_timestamp = int(data.get("to_timestamp"))
    request_interval = data.get("group_by")

    return measurements, sensors, from_timestamp, to_timestamp, request_interval


# Internal API: _resolve_sensors
def _resolve_sensors(sensors):
    available_sensors = get_available_sensors()

    if not sensors:
        return available_sensors
    return _build_matched_sensors(sensors, available_sensors)


# Internal API: _resolve_interval
def _resolve_interval(request_interval, start, end):
    if request_interval:
        return request_interval
    duration = (end - start) / 1000
    if duration > (7 * 24 * 3600):
        return "1h"
    if duration > (24 * 3600):
        return "5m"
    return "1m"


# # Internal API: get_interval
# def _get_default_interval(start, end):
#     duration = (end - start) / 1000
#     if duration > (7 * 24 * 3600):
#         return "1h"
#     if duration > (24 * 3600):
#         return "5m"
#     return "1m"


# Internal API: _build_telemetry_query
def _build_telemetry_query(measurement, sensors, start, end, interval):
    if sensors is None:
        return None

    sensor_expr = ", ".join([f'mean("{sensor}")' for sensor in sensors])
    query = f"""
    SELECT {sensor_expr}
    FROM "{measurement}"
    WHERE time >= {str(start)}ms AND time <= {str(end)}ms
    GROUP BY time({interval}) fill(null) ORDER BY time ASC
    """
    return query


# Internal API: match_sensors
def _build_matched_sensors(sensors, available_sensors):
    result = []

    sensor_set = set(sensors)
    for item in available_sensors:
        matched = [s for s in item.get("sensors") if s in sensor_set]
        if matched:
            result.append({"measurement": item.get("measurement"), "sensors": matched})

    return result


# Internal API: _fetch_telemetry
def _fetch_telemetry(db_client, matched_sensors, from_ts, to_ts, interval):  # pylint: disable=too-many-locals
    telemetry_data = {}

    for measurement in matched_sensors:
        measurement_name = measurement.get("measurement")
        sensors = measurement.get("sensors")
        query = _build_telemetry_query(
            measurement_name, sensors, from_ts, to_ts, interval
        )

        if not query:
            continue
        query_result = db_client.query(query)
        if len(query_result) > 0:
            points = []
            for series in query_result.raw.get("series", []):
                columns = series["columns"]
                for row in series["values"]:
                    record = dict(zip(columns, row))
                    points.append(record)
            telemetry_data[measurement_name] = points
    return telemetry_data


# Internal API: write_data
def _create_compressed_file(data, output_path):
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
def download_telemetry_file() -> Response:
    """
    Sending file and deleting it after finishing process

    Query parameter:
        - filename: string

    Returns:
        File Object: File object that matches given name
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
