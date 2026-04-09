"""
This module provides the features to access proxy telemetry database via QDMI
"""

from flask import Blueprint, request, send_file, send_from_directory, after_this_request, Response
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

BLUEPRINT = Blueprint("telemetry", __name__)

# Define constants
CURRENT_DIRECTORY = os.getcwd()
UPLOAD_FOLDER = CURRENT_DIRECTORY + "/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CHUNK_SIZE = 1024 * 1024
EXPIRY_TIME = 3600
DELAY_TIME = 300

# Convert a result of SQL query to list()
# Args: ResultSet()
# Return: list()
def _sanitized_query_result(data):
    result = []
    for data_source in data:
        for point in data_source:
            result.append(point)

    return result


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
        

# API: get_available_sensors 
# Desc: Request to get available sensors of each measurement
# Return: sensors list
@BLUEPRINT.get("/telemetry/sensors")
@jwt_required()
@log_call
def get_available_sensors():
    try:
        client = _open_influxdb()
        measurements_list = client.get_list_measurements()
        measurements = [] # list()
        for item in measurements_list:
            measurement_name = item.get('name')
            sensors = client.query(f'SHOW FIELD KEYS FROM {measurement_name}')
            measurement_sensors = []
            for sensor in sensors.get_points():
                measurement_sensors.append(sensor.get('fieldKey'))
            measurements.append({"name": measurement_name, "sensors": measurement_sensors})
        client.close()
        return measurements
    except TypeError as error:
        return {"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR

# API: delete_file_later()
# Desc: Delete file after delay time
def delete_file_later(file_path, delay=DELAY_TIME):
    def task():
        time.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print("Deleted:", file_path)
        except Exception as e:
            print("Error deleting:", e)

    threading.Thread(target=task).start()

# API: generate_and_delete()
# Desc: Send file and delete it 
# Return: sensors list
@BLUEPRINT.post("/telemetry/download/")
@jwt_required()
@log_call
def download_file():
    requestData = request.get_json()
    filename = requestData.get("filename")
    #filepath = os.path.join(UPLOAD_FOLDER, filename)
    #filesize = os.path.getsize(filepath)
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

    """
    if filesize <= CHUNK_SIZE:
        # schedule deletion after DELAY_TIME seconds
        #delete_file_later(filepath, delay=DELAY_TIME)
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    else:
        ## Streaming large file
        try:
            with gzip.open(filepath, "rb") as f:
                while chunk:= f.read(CHUNK_SIZE):
                    yield chunk
        finally:
            try:
                os.remove(filepath)
                print("File deleted")
            except Exception as e:
                    print("Error deleting file:", e)
    """

# API: get_telemetry_data
# args: user's input
# Desc: Request to get Telemetry data
# Return: list of data sources
@BLUEPRINT.post("/telemetry")
@jwt_required()
@log_call
def get_telemetry_data():
    """Request to get data from influxDB"""
    request_data = request.get_json()
    measurements = request_data.get("measurements")
    print("measurements:")
    print(measurements)
    from_timestamp = request_data.get("from_timestamp")
    to_timestamp = request_data.get("to_timestamp")
    group_by = request_data.get("group_by")


    if measurements == None or len(measurements) == 0:
        measurements = get_available_sensors()

    try:     
        # Query data   
        client = _open_influxdb()
        telemetry_data = {} # dict()
        for measurement in measurements:
            measurement_name = measurement.get('name')
            sensors = measurement.get('sensors')
            measurement_data = {} # dict()
            for sensor in sensors:                   
                #query = 'SELECT * FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms fill(null) ORDER BY time ASC'
                query = 'SELECT mean("' + sensor + '") FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms GROUP BY time(' + group_by + ') fill(null) ORDER BY time ASC'
                #query = 'SELECT "' + sensor + '" FROM "' + measurement_name + '" WHERE time >= ' + str(from_timestamp) + 'ms and time <= ' + str(to_timestamp) + 'ms fill(null) ORDER BY time ASC'
                sensor_data = client.query(query)                
                data = _sanitized_query_result(sensor_data)
                measurement_data.update({sensor: data})
            telemetry_data.update({measurement_name: measurement_data})
        client.close()
        
        # Save data to file
        filename = f"{int(time.time())}_telemetry.json.gz"
        #filename = secure_filename('telemetry_' + str(from_timestamp) + '_' + str(to_timestamp) + '.json.gz')
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # write compressed data        
        compressed_data = str.encode((json.dumps(telemetry_data)))
        with gzip.open(file_path, 'wb') as f:
            f.write(compressed_data)
        filesize = os.path.getsize(file_path)
        return {
            "filesize": filesize,
            "filename": filename
        }, HTTPStatus.OK
        #return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
        # return Response with large file
        # return Response(
        #     generate_and_delete(file_path),
        #     mimetype="application/octet-stream",
        #     headers={
        #         "Content-Disposition": f"attachment; filename={filename}"
        #     }
        # )
    
    except TypeError as error:
        return {
            "error": str(error)
        }, HTTPStatus.INTERNAL_SERVER_ERROR
   

