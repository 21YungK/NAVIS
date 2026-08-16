from tools import list_files
from tools import list_flight_logs

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