from tools import list_files
from tools import list_flight_logs
from tools import list_flight_logs, inspect_flight_log
import tools

def test_invalid_directory():
    result = list_files("this_folder_should_not_exist")

    assert result["success"] is False
    assert result["error"] == "Directory does not exist"


def test_valid_directory(tmp_path):
    test_file = tmp_path / "flight_log.txt"
    test_file.write_text("test data")

    result = list_files(tmp_path)

    assert result["success"] is True
    assert "flight_log.txt" in result["files"]


def test_does_not_return_directories(tmp_path):
    subfolder = tmp_path / "logs"
    subfolder.mkdir()

    test_file = tmp_path / "main.py"
    test_file.write_text("print('test')")

    result = list_files(tmp_path)

    assert result["success"] is True
    assert "main.py" in result["files"]
    assert "logs" not in result["files"]


def test_list_flight_logs():
    logs = list_flight_logs()

    assert isinstance(logs, list)
    assert "sample_flight.csv" in logs
    assert "sample_px4.ulg" in logs
    assert "sample_ardupilot.bin" in logs


def test_inspect_flight_log_csv():
    result = inspect_flight_log("sample_flight.csv")

    assert result["filename"] == "sample_flight.csv"
    assert result["format"] == "csv"
    assert result["rows"] == 3
    assert "timestamp" in result["columns"]
    assert "altitude" in result["columns"]
    assert "battery_voltage" in result["columns"]

def test_inspect_flight_log_missing_file():
    result = inspect_flight_log("does_not_exist.csv")

    assert result["error"] == "File not found"

def test_inspect_invalid_ulg():
    result = inspect_flight_log("sample_px4.ulg")

    assert "error" in result

# Testing the calculation logic itself
def test_flight_summary_ulg(monkeypatch, tmp_path):
    fake_log = tmp_path / "test.ulg"
    fake_log.write_bytes(b"fake")

    monkeypatch.setattr(tools, "DATA_DIR", tmp_path)

    class FakeDataset:
        def __init__(self, data):
            self.data = data

    class FakeULog:
        start_timestamp = 1_000_000
        last_timestamp = 11_000_000

        def __init__(self, path):
            pass

        def get_dataset(self, name):
            datasets = {
                "battery_status": FakeDataset({
                    "voltage_v": [24.0, 23.5, 22.0]
                }),
                "vehicle_global_position": FakeDataset({
                    "alt": [50.0, 75.0, 100.0]
                }),
                "vehicle_gps_position": FakeDataset({
                    "satellites_used": [20, 18, 22]
                }),
            }

            return datasets[name]

    monkeypatch.setattr(tools, "ULog", FakeULog)

    result = tools.flight_summary("test.ulg")

    assert result["duration_seconds"] == 10.0

    assert result["battery"]["start_voltage_v"] == 24.0
    assert result["battery"]["end_voltage_v"] == 22.0
    assert result["battery"]["minimum_voltage_v"] == 22.0

    assert result["altitude"]["maximum_m"] == 100.0

    assert result["gps"]["minimum_satellites"] == 18