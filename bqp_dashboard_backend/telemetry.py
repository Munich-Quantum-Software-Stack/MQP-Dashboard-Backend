"""
This module provides the features to access proxy telemetry database via QDMI
"""

from flask import Blueprint, request, send_file, send_from_directory, after_this_request, Response, stream_with_context
from flask_jwt_extended import jwt_required
from http import HTTPStatus
from eliot import log_call
import json
import threading
import os, gzip, time
from werkzeug.utils import secure_filename
import shutil
import influxdb
from influxdb import InfluxDBClient
from io import BytesIO

BLUEPRINT = Blueprint("telemetry", __name__)

# Define constants
BASE_DIR = os.getcwd()
#BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CHUNK_SIZE = 1024 * 1024
EXPIRY_TIME = 3600 # seconds
DELAY_TIME = 60 # seconds
SENSOR_MAP_CACHE = {
    "data": [],
    "timestamp": 0
}
CACHE_TTL = 300 # seconds


# Open connection to InfluxDB
def _open_influxdb():
    try:
        client = InfluxDBClient(
            host = os.getenv("INFLUX_HOST"),
            port = os.getenv("INFLUX_PORT"),
            database = os.getenv("INFLUX_DATABASE"),
            username = os.getenv("INFLUX_USERNAME"),
            password = os.getenv("INFLUX_PASSWORD"),
        )
        return client
    except TypeError as err:
        return {str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR
        
#-------------------------------------------------------------------
# API: get_available_sensors 
# Desc: Request to get available sensors of each measurement, refresh every CACHE_TTL seconds
# Return: sensors list
#-------------------------------------------------------------------
@BLUEPRINT.get("/telemetry/sensors")
@jwt_required()
@log_call
def get_available_sensors():
    global SENSOR_MAP_CACHE
    now = time.time()

    if SENSOR_MAP_CACHE["data"] is None or (now - SENSOR_MAP_CACHE["timestamp"] > CACHE_TTL):
        SENSOR_MAP_CACHE["data"] = build_sensor_map()
        SENSOR_MAP_CACHE["timestamp"] = now

    return SENSOR_MAP_CACHE["data"]

# Internal API: get_measurements
def get_measurements(client):
    return client.get_list_measurements()
 
 # Internal API: get_sensors_from_measurement()
def get_sensors_from_measurement(client, measurement):
    return client.query(f'SHOW FIELD KEYS FROM {measurement}')

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
    sensor_map = [] # list()
    try:
        client = _open_influxdb()
        measurements_list = get_measurements(client)
        for item in measurements_list:
            measurement_name = item.get('name')
            sensors = get_sensors_from_measurement(client, measurement_name)
            measurement_sensors = []
            for sensor in sensors.get_points():
                measurement_sensors.append(sensor.get('fieldKey'))
            sensor_map.append({"measurement": measurement_name, "sensors": measurement_sensors})
        client.close()
        return sensor_map
    except TypeError as error:
        return {"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR



#-------------------------------------------------------------------
# API: get_telemetry_data
# args: user's input
# Desc: Request to get Telemetry data
# Return: list of data sources
#-------------------------------------------------------------------
@BLUEPRINT.post("/telemetry")
@jwt_required()
@log_call
def get_telemetry_data():
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
        measurement_name = measurement.get('measurement')
        sensors = measurement.get('sensors')
        # for sensor in sensors:                   
        #     #query = 'SELECT * FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms fill(null) ORDER BY time ASC'
        #     query = 'SELECT mean("' + sensor + '") FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms GROUP BY time(' + interval + ') fill(null) ORDER BY time ASC'
        #     #query = 'SELECT "' + sensor + '" FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms fill(null) ORDER BY time ASC'
        #     query_result = client.query(query)
        #     print("query_result:")
        #     print(query_result)
        query = build_telemetry_query(measurement_name, sensors, from_timestamp, to_timestamp, interval)

        if not query:
            continue
        query_result = client.query(query)
        # print("query_result:")
        # print(query_result)
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
    return {
        "filesize": filesize,
        "filename": filename
    }, HTTPStatus.OK
    
# Internal API: get_interval 
def get_default_interval(start, end):
    duration = end - start
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
   
    sensor_expr = ", " .join([f'mean("{sensor}")' for sensor in sensors])
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
    #compressed_data = str.encode((json.dumps(data)))
    with gzip.open(output_path, 'wt', encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return output_path

#-------------------------------------------------------------------
# API: download_telemetry_file
# args: filename
# Desc: Sending telemetry file and delete it after downloading
# Return: File
#-------------------------------------------------------------------
@BLUEPRINT.get("/telemetry/download")
def download_telemetry_file():
    filename = request.args.get("filename")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return {"error": "File not found"}, 404

    def generate():
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
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


"""
@BLUEPRINT.post("/telemetry/download")
@jwt_required()
@log_call
def download_telemetry_file():  
    data = request.get_json()
    filename = data.get("filename")
    # print("filename: " + filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}, HTTPStatus.NOT_FOUND
    
    filesize = os.path.getsize(file_path)
    # Small file → normal send
    if filesize <= CHUNK_SIZE:
        # schedule deletion after DELAY_TIME seconds
        delete_file_after_delay(file_path, delay=DELAY_TIME)
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    
    # Large file → streaming
    def generate():
        ## Streaming large file
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break;
                    yield chunk
        finally:
            try:
                os.remove(file_path)
                print("File deleted")
            except Exception as e:
                print("Error deleting file:", e)
    return Response(
        stream_with_context(generate()),
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/gzip",
        },
        status = HTTPStatus.OK
    )   
   
# Internal API: delete_file_after_delay
def delete_file_after_delay(filepath, delay):
    def task():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print("Deleted:", filepath)
        except Exception as e:
            print("Error deleting:", e)

    threading.Thread(target=task).start()
"""