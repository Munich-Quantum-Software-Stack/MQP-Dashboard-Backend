import gzip
import importlib.util
import json
import sys
import types
from pathlib import Path


class _DummyBlueprint:
    def __init__(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def post(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


def _dummy_send_file(*args, **kwargs):
    return None


def _dummy_send_from_directory(*args, **kwargs):
    return None


def _dummy_after_this_request(func):
    return func


sys.modules["flask"] = types.SimpleNamespace(
    Blueprint=_DummyBlueprint,
    request=None,
    Response=object,
    stream_with_context=lambda value: value,
    send_file=_dummy_send_file,
    send_from_directory=_dummy_send_from_directory,
    after_this_request=_dummy_after_this_request,
)

sys.modules.setdefault(
    "flask_jwt_extended",
    types.SimpleNamespace(jwt_required=lambda *a, **k: (lambda f: f)),
)
sys.modules.setdefault("eliot", types.SimpleNamespace(log_call=lambda f: f))
sys.modules.setdefault("influxdb", types.SimpleNamespace(InfluxDBClient=object))

TELEMETRY_PATH = (
    Path(__file__).resolve().parents[1] / "bqp_dashboard_backend" / "telemetry.py"
)
spec = importlib.util.spec_from_file_location("telemetry", TELEMETRY_PATH)
telemetry = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(telemetry)


def test_get_default_interval_returns_1h_for_duration_over_7_days():
    start = 0
    end = (7 * 24 * 3600 + 1) * 1000

    assert telemetry.get_default_interval(start, end) == "1h"


def test_get_default_interval_returns_5m_for_duration_over_1_day_and_up_to_7_days():
    start = 0
    end = (24 * 3600 + 1) * 1000

    assert telemetry.get_default_interval(start, end) == "5m"


def test_get_default_interval_returns_1m_for_duration_up_to_1_day():
    start = 0
    end = 24 * 3600 * 1000

    assert telemetry.get_default_interval(start, end) == "1m"


def test_build_matched_sensors_returns_only_matching_sensors_grouped_by_measurement():
    requested_sensors = ["temperature", "pressure", "not_available"]
    available_sensors = [
        {"measurement": "m1", "sensors": ["temperature", "humidity"]},
        {"measurement": "m2", "sensors": ["pressure", "voltage"]},
        {"measurement": "m3", "sensors": ["current"]},
    ]

    matched = telemetry.build_matched_sensors(requested_sensors, available_sensors)

    assert matched == [
        {"measurement": "m1", "sensors": ["temperature"]},
        {"measurement": "m2", "sensors": ["pressure"]},
    ]


def test_build_matched_sensors_returns_empty_when_no_sensor_matches():
    requested_sensors = ["x", "y"]
    available_sensors = [{"measurement": "m1", "sensors": ["a", "b"]}]

    assert telemetry.build_matched_sensors(requested_sensors, available_sensors) == []


def test_build_telemetry_query_returns_none_when_sensors_is_none():
    assert telemetry.build_telemetry_query("measurement", None, 1, 2, "1m") is None


def test_build_telemetry_query_builds_expected_query_string():
    query = telemetry.build_telemetry_query(
        measurement="machine.telemetry",
        sensors=["temperature", "pressure"],
        start=1000,
        end=2000,
        interval="5m",
    )

    assert 'SELECT mean("temperature"), mean("pressure")' in query
    assert 'FROM "machine.telemetry"' in query
    assert "WHERE time >= 1000ms AND time <= 2000ms" in query
    assert "GROUP BY time(5m) fill(null) ORDER BY time ASC" in query


def test_create_compressed_file_writes_gzip_json_and_returns_output_path(tmp_path):
    data = {
        "measurement": [
            {"time": "2024-01-01T00:00:00Z", "temperature": 18.5},
            {"time": "2024-01-01T00:01:00Z", "temperature": 18.7},
        ]
    }
    output_path = tmp_path / "telemetry.json.gz"

    returned_path = telemetry.create_compressed_file(data, str(output_path))

    assert returned_path == str(output_path)
    assert output_path.exists()

    with gzip.open(output_path, "rt", encoding="utf-8") as f:
        content = json.load(f)

    assert content == data
