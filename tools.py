import csv
from pathlib import Path
from pyulog import ULog

DATA_DIR = Path(__file__).parent / "data"


def list_flight_logs():
    if not DATA_DIR.exists():
        return []

    allowed_extensions = {
    ".ulg",
    ".bin",
    ".csv",
    ".tlog",
    ".json",
    ".log",
}
    return sorted(
        file.name
        for file in DATA_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in allowed_extensions
    )

def list_files(directory="."):
    """
    Return files contained in a directory.
    """

    path = Path(directory)

    if not path.exists():
        return {
            "success": False,
            "error": "Directory does not exist",
        }

    if not path.is_dir():
        return {
            "success": False,
            "error": "Path is not a directory",
        }

    files = [
        item.name
        for item in path.iterdir()
        if item.is_file()
    ]

    return {
        "success": True,
        "files": files,
    }

def inspect_flight_log(filename: str):
    path = DATA_DIR / filename

    if not path.exists():
        return {"error": "File not found"}

    suffix = path.suffix.lower()

    if suffix == ".csv":
        with open(path, newline="", encoding="utf-8") as file:
            reader = csv.reader(file)

            headers = next(reader, [])
            row_count = sum(1 for _ in reader)

        return {
            "filename": filename,
            "format": "csv",
            "rows": row_count,
            "columns": headers,
        }

    if suffix == ".ulg":
        try:
            ulog = ULog(str(path))

            topics = sorted({
                dataset.name
                for dataset in ulog.data_list
            })

            return {
                "filename": filename,
                "format": "ulg",
                "topic_count": len(topics),
                "topics": topics,
                "start_timestamp": ulog.start_timestamp,
                "last_timestamp": ulog.last_timestamp,
            }

        except Exception as exc:
            return {
                "error": f"Failed to parse ULog: {exc}"
            }

    return {
        "error": f"Unsupported format: {suffix}"
    }