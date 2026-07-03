import gzip
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


class FakeAction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeInfluxQueryResult:
    def __init__(self, raw):
        self.raw = raw

    def __len__(self):
        return len(self.raw.get("series", []))


class FakeSensorsResult:
    def __init__(self, points):
        self._points = points

    def get_points(self):
        return iter(self._points)


def _identity_decorator(func):
    return func


def _log_call(func=None, *args, **kwargs):
    if func is None:
        return _identity_decorator
    return func


TELEMETRY_PATH = (
    Path(__file__).resolve().parents[1] / "mqp_dashboard_backend" / "telemetry.py"
)


@pytest.fixture
def telemetry_module(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "influxdb",
        types.SimpleNamespace(InfluxDBClient=object),
    )

    if importlib.util.find_spec("eliot") is None:
        monkeypatch.setitem(
            sys.modules,
            "eliot",
            types.SimpleNamespace(
                add_destinations=lambda *args, **kwargs: None,
                log_call=_log_call,
                start_action=lambda *args, **kwargs: FakeAction(),
                to_file=lambda *args, **kwargs: None,
            ),
        )

    sys.modules.pop("mqp_dashboard_backend.telemetry", None)
    spec = importlib.util.spec_from_file_location(
        "mqp_dashboard_backend.telemetry", TELEMETRY_PATH
    )
    assert spec is not None and spec.loader is not None

    telemetry = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "mqp_dashboard_backend.telemetry", telemetry)
    spec.loader.exec_module(telemetry)

    return telemetry


def test_resolve_interval_returns_1h_for_duration_over_7_days(telemetry_module):
    start = 0
    end = (7 * 24 * 3600 + 1) * 1000

    assert telemetry_module._resolve_interval(None, start, end) == "1h"


def test_resolve_interval_returns_5m_for_duration_over_1_day_and_up_to_7_days(
    telemetry_module,
):
    start = 0
    end = (24 * 3600 + 1) * 1000

    assert telemetry_module._resolve_interval(None, start, end) == "5m"


def test_resolve_interval_returns_1m_for_duration_up_to_1_day(telemetry_module):
    start = 0
    end = 24 * 3600 * 1000

    assert telemetry_module._resolve_interval(None, start, end) == "1m"


def test__build_matched_sensors_returns_only_matching_sensors_grouped_by_measurement(
    telemetry_module,
):
    requested_sensors = ["temperature", "pressure", "not_available"]
    available_sensors = [
        {"measurement": "m1", "sensors": ["temperature", "humidity"]},
        {"measurement": "m2", "sensors": ["pressure", "voltage"]},
        {"measurement": "m3", "sensors": ["current"]},
    ]

    matched = telemetry_module._build_matched_sensors(
        requested_sensors, available_sensors
    )

    assert matched == [
        {"measurement": "m1", "sensors": ["temperature"]},
        {"measurement": "m2", "sensors": ["pressure"]},
    ]


def test__build_matched_sensors_returns_empty_when_no_sensor_matches(telemetry_module):
    requested_sensors = ["x", "y"]
    available_sensors = [{"measurement": "m1", "sensors": ["a", "b"]}]

    assert (
        telemetry_module._build_matched_sensors(requested_sensors, available_sensors)
        == []
    )


def test__build_telemetry_query_returns_none_when_sensors_is_none(telemetry_module):
    assert (
        telemetry_module._build_telemetry_query("measurement", None, 1, 2, "1m") is None
    )


def test__build_telemetry_query_builds_expected_query_string(telemetry_module):
    query = telemetry_module._build_telemetry_query(
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


def test__create_compressed_file_returns_output_path(tmp_path, telemetry_module):
    data = {"measurement": [{"temperature": 18.5}]}
    output_path = tmp_path / "telemetry.json.gz"

    returned_path = telemetry_module._create_compressed_file(data, str(output_path))

    assert returned_path == str(output_path)


def test__create_compressed_file_writes_expected_gzip_json(tmp_path, telemetry_module):
    data = {
        "measurement": [
            {"time": "2024-01-01T00:00:00Z", "temperature": 18.5},
            {"time": "2024-01-01T00:01:00Z", "temperature": 18.7},
        ]
    }
    output_path = tmp_path / "telemetry.json.gz"

    telemetry_module._create_compressed_file(data, str(output_path))

    with gzip.open(output_path, "rt", encoding="utf-8") as f:
        content = json.load(f)

    assert content == data


def test__open_influxdb_passes_environment_to_client(monkeypatch, telemetry_module):
    captured_kwargs = {}

    class FakeInfluxDBClient:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setenv("PROXY_DB_HOST", "influx.example.test")
    monkeypatch.setenv("PROXY_DB_PORT", "8086")
    monkeypatch.setenv("PROXY_DB", "telemetry")
    monkeypatch.setenv("PROXY_DB_USER", "dashboard")
    monkeypatch.setenv("PROXY_DB_PASS", "secret")
    monkeypatch.setattr(telemetry_module, "InfluxDBClient", FakeInfluxDBClient)

    client = telemetry_module._open_influxdb()

    assert isinstance(client, FakeInfluxDBClient)
    assert captured_kwargs == {
        "host": "influx.example.test",
        "port": "8086",
        "database": "telemetry",
        "username": "dashboard",
        "password": "secret",
    }


def test__open_influxdb_wraps_type_error(monkeypatch, telemetry_module):
    class BrokenInfluxDBClient:
        def __init__(self, **kwargs):
            raise TypeError("invalid influx configuration")

    monkeypatch.setattr(telemetry_module, "InfluxDBClient", BrokenInfluxDBClient)

    with pytest.raises(telemetry_module.TelemetryError) as exc_info:
        telemetry_module._open_influxdb()

    assert str(exc_info.value) == "invalid influx configuration"


def test__get_measurements_delegates_to_influx_client(telemetry_module):
    class FakeClient:
        def get_list_measurements(self):
            return [{"name": "cpu"}, {"name": "memory"}]

    assert telemetry_module._get_measurements(FakeClient()) == [
        {"name": "cpu"},
        {"name": "memory"},
    ]


def test__get_sensors_from_measurement_queries_field_keys(telemetry_module):
    class FakeClient:
        def __init__(self):
            self.queries = []

        def query(self, query):
            self.queries.append(query)
            return FakeSensorsResult([{"fieldKey": "temperature"}])

    client = FakeClient()

    result = telemetry_module._get_sensors_from_measurement(client, "machine")

    assert list(result.get_points()) == [{"fieldKey": "temperature"}]
    assert client.queries == ["SHOW FIELD KEYS FROM machine"]


def test__build_sensor_map_fetches_measurements_and_fields(
    monkeypatch, telemetry_module
):
    class FakeClient:
        def __init__(self):
            self.closed = False

        def get_list_measurements(self):
            return [{"name": "machine"}, {"name": "rack"}]

        def query(self, query):
            if query == "SHOW FIELD KEYS FROM machine":
                return FakeSensorsResult(
                    [{"fieldKey": "temperature"}, {"fieldKey": "pressure"}]
                )
            if query == "SHOW FIELD KEYS FROM rack":
                return FakeSensorsResult([{"fieldKey": "humidity"}])
            raise AssertionError(f"unexpected query: {query}")

        def close(self):
            self.closed = True

    fake_client = FakeClient()
    monkeypatch.setattr(telemetry_module, "_open_influxdb", lambda: fake_client)

    sensor_map = telemetry_module._build_sensor_map()

    assert sensor_map == [
        {"measurement": "machine", "sensors": ["temperature", "pressure"]},
        {"measurement": "rack", "sensors": ["humidity"]},
    ]
    assert fake_client.closed is True


def test__resolve_sensors_returns_all_available_when_request_is_empty(
    monkeypatch, telemetry_module
):
    available_sensors = [
        {"measurement": "machine", "sensors": ["temperature", "pressure"]}
    ]
    monkeypatch.setattr(
        telemetry_module, "get_available_sensors", lambda: available_sensors
    )

    assert telemetry_module._resolve_sensors([]) == available_sensors


def test__resolve_sensors_filters_requested_sensors(monkeypatch, telemetry_module):
    monkeypatch.setattr(
        telemetry_module,
        "get_available_sensors",
        lambda: [
            {"measurement": "machine", "sensors": ["temperature", "pressure"]},
            {"measurement": "rack", "sensors": ["humidity"]},
        ],
    )

    assert telemetry_module._resolve_sensors(["humidity", "missing"]) == [
        {"measurement": "rack", "sensors": ["humidity"]}
    ]


def test__fetch_telemetry_builds_queries_and_maps_series_rows(telemetry_module):
    class FakeClient:
        def __init__(self):
            self.queries = []

        def query(self, query):
            self.queries.append(query)
            if 'FROM "empty"' in query:
                return FakeInfluxQueryResult({"series": []})
            return FakeInfluxQueryResult(
                {
                    "series": [
                        {
                            "columns": [
                                "time",
                                "mean_temperature",
                                "mean_pressure",
                            ],
                            "values": [
                                ["2026-01-01T00:00:00Z", 18.5, 101.2],
                                ["2026-01-01T00:01:00Z", 18.6, 101.1],
                            ],
                        }
                    ]
                }
            )

    matched_sensors = [
        {"measurement": "machine", "sensors": ["temperature", "pressure"]},
        {"measurement": "skip", "sensors": None},
        {"measurement": "empty", "sensors": ["humidity"]},
    ]

    telemetry_data = telemetry_module._fetch_telemetry(
        FakeClient(), matched_sensors, 1000, 2000, "1m"
    )

    assert telemetry_data == {
        "machine": [
            {
                "time": "2026-01-01T00:00:00Z",
                "mean_temperature": 18.5,
                "mean_pressure": 101.2,
            },
            {
                "time": "2026-01-01T00:01:00Z",
                "mean_temperature": 18.6,
                "mean_pressure": 101.1,
            },
        ]
    }


def test_download_telemetry_file_streams_file_and_removes_it(
    tmp_path, monkeypatch, telemetry_module
):
    from flask import Flask

    upload_folder = tmp_path / "uploads"
    upload_folder.mkdir()
    telemetry_file = upload_folder / "telemetry.json.gz"
    telemetry_file.write_bytes(b"compressed telemetry")
    monkeypatch.setattr(telemetry_module, "UPLOAD_FOLDER", str(upload_folder))
    monkeypatch.setattr(telemetry_module, "CHUNK_FILE_SIZE", 4)

    app = Flask(__name__)
    app.register_blueprint(telemetry_module.BLUEPRINT)

    response = app.test_client().get(
        "/telemetry/download", query_string={"filename": telemetry_file.name}
    )

    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == (
        "attachment; filename=telemetry.json.gz"
    )
    assert response.headers["Content-Type"] == "application/gzip"
    assert response.data == b"compressed telemetry"
    assert not telemetry_file.exists()


def test_download_telemetry_file_returns_not_found_for_missing_file(
    tmp_path, monkeypatch, telemetry_module
):
    from flask import Flask

    monkeypatch.setattr(telemetry_module, "UPLOAD_FOLDER", str(tmp_path))
    app = Flask(__name__)
    app.register_blueprint(telemetry_module.BLUEPRINT)

    response = app.test_client().get(
        "/telemetry/download", query_string={"filename": "missing.json.gz"}
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "File not found"}
