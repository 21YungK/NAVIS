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

def flight_summary(filename: str):
    path = DATA_DIR / filename

    if not path.exists():
        return {"error": "File not found"}

    if path.suffix.lower() != ".ulg":
        return {"error": "Flight summary currently supports .ulg files only"}

    try:
        ulog = ULog(str(path))

        duration_seconds = (
            ulog.last_timestamp - ulog.start_timestamp
        ) / 1_000_000

        battery = ulog.get_dataset("battery_status").data
        global_position = ulog.get_dataset("vehicle_global_position").data
        gps = ulog.get_dataset("vehicle_gps_position").data

        voltage = battery["voltage_v"]
        altitude = global_position["alt"]
        satellites = gps["satellites_used"]

        return {
            "filename": filename,
            "duration_seconds": round(duration_seconds, 2),

            "battery": {
                "start_voltage_v": round(float(voltage[0]), 2),
                "end_voltage_v": round(float(voltage[-1]), 2),
                "minimum_voltage_v": round(float(min(voltage)), 2),
            },

            "altitude": {
                "maximum_m": round(float(max(altitude)), 2),
            },

            "gps": {
                "minimum_satellites": int(min(satellites)),
            },
        }

    except Exception as exc:
        return {
            "error": f"Failed to summarize ULog: {exc}"
        }
def correlate_anomalies(anomalies, window_seconds=1.0):
    correlations = []

    voltage_events = [
        event for event in anomalies
        if event["type"] == "battery_voltage_sag"
    ]

    current_events = [
        event for event in anomalies
        if event["type"] == "high_current"
    ]

    for voltage_event in voltage_events:
        for current_event in current_events:
            time_difference = abs(
                voltage_event["timestamp_s"]
                - current_event["timestamp_s"]
            )

            if time_difference <= window_seconds:
                voltage_drop_pct = (
                    (
                        voltage_event["threshold_v"]
                        - voltage_event["value_v"]
                    )
                    / voltage_event["threshold_v"]
                ) * 100

                severity = "medium"

                if (
                    voltage_drop_pct >= 4
                    or current_event["value_a"]
                    >= current_event["threshold_a"] * 1.1
                ):
                    severity = "high"

                correlations.append({
                    "type": "power_event",
                    "timestamp_s": round(
                        min(
                            voltage_event["timestamp_s"],
                            current_event["timestamp_s"],
                        ),
                        2,
                    ),
                    "severity": severity,
                    "time_difference_s": round(time_difference, 2),
                    "voltage_v": voltage_event["value_v"],
                    "current_a": current_event["value_a"],
                    "diagnosis": (
                        "High current draw coincided with a battery "
                        "voltage sag, indicating a possible high-load "
                        "power event."
                    ),
                })

    return correlations


def detect_anomalies(filename: str):
    path = DATA_DIR / filename

    if not path.exists():
        return {"error": "File not found"}

    if path.suffix.lower() != ".ulg":
        return {"error": "Anomaly detection currently supports .ulg files only"}

    try:
        ulog = ULog(str(path))

        battery = ulog.get_dataset("battery_status").data
        gps = ulog.get_dataset("vehicle_gps_position").data

        anomalies = []

        # Battery data
        timestamps = battery["timestamp"]
        voltage = battery["voltage_v"]
        current = battery["current_a"]

        starting_voltage = float(voltage[0])
        low_voltage_threshold = starting_voltage * 0.80

        # Detect lowest voltage sag
        minimum_voltage = float(min(voltage))

        if minimum_voltage < low_voltage_threshold:
            index = list(voltage).index(min(voltage))

            timestamp_s = (
                float(timestamps[index]) - ulog.start_timestamp
            ) / 1_000_000

            anomalies.append({
                "type": "battery_voltage_sag",
                "timestamp_s": round(timestamp_s, 2),
                "value_v": round(minimum_voltage, 2),
                "threshold_v": round(low_voltage_threshold, 2),
            })

        # Detect highest current spike
        maximum_current = float(max(current))
        high_current_threshold = 45.0

        if maximum_current > high_current_threshold:
            index = list(current).index(max(current))

            timestamp_s = (
                float(timestamps[index]) - ulog.start_timestamp
            ) / 1_000_000

            anomalies.append({
                "type": "high_current",
                "timestamp_s": round(timestamp_s, 2),
                "value_a": round(maximum_current, 2),
                "threshold_a": high_current_threshold,
            })

        # Detect poor GPS reception
        gps_timestamps = gps["timestamp"]
        satellites = gps["satellites_used"]

        minimum_satellites = int(min(satellites))
        low_gps_threshold = 10

        if minimum_satellites < low_gps_threshold:
            index = list(satellites).index(min(satellites))

            timestamp_s = (
                float(gps_timestamps[index]) - ulog.start_timestamp
            ) / 1_000_000

            anomalies.append({
                "type": "low_gps_satellites",
                "timestamp_s": round(timestamp_s, 2),
                "satellites": minimum_satellites,
                "threshold": low_gps_threshold,
            })
        correlations = correlate_anomalies(anomalies)
        return {
            "filename": filename,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "correlation_count": len(correlations),
            "correlations": correlations,
        }

    except Exception as exc:
        return {
            "error": f"Failed to analyze ULog: {exc}"
        }


