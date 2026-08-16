# NAVIS

**Drone flight log analysis and diagnostic toolkit built in Python.**

NAVIS is a personal project I am building to explore automated analysis of drone flight telemetry.

Flight logs can contain thousands of samples across battery, GPS, attitude, position, motor outputs, estimator states, and other systems. NAVIS provides tools for turning that raw telemetry into structured flight summaries, detecting unusual events, and investigating the surrounding flight conditions.

The project currently focuses on **PX4 ULog (`.ulg`) flight data**, with support for additional flight stacks planned.

## Why I Built It

I've been interested in quadcopters for years, especially FPV drones and the technical side of building, tuning, flying, and troubleshooting them. That interest is what pushed me toward working with flight data and understanding what is actually happening inside a vehicle during flight.

My original idea for NAVIS was fairly simple: load a drone flight log and automatically identify anything unusual.

As I started working with real PX4 telemetry, I realized that detecting a threshold violation is only the first part of diagnosing a flight.

For example, a sudden battery voltage drop might indicate a power problem. But that same voltage drop could also happen during an aggressive maneuver when the motors are demanding significantly more power.

That led me toward a more contextual analysis pipeline:

```text
Flight Log
    |
    v
Parse Telemetry
    |
    v
Summarize Flight
    |
    v
Detect Anomalies
    |
    v
Correlate Related Events
    |
    v
Inspect Surrounding Telemetry
    |
    v
Evaluate Flight Context
    |
    v
Diagnose Event
```

Instead of treating individual telemetry values as isolated warnings, NAVIS attempts to determine what the aircraft was doing when the event occurred.

## Current Capabilities

NAVIS currently supports:

- PX4 `.ulg` parsing with PyULog
- Generic CSV telemetry inspection
- Automatic flight log discovery
- PX4 topic discovery
- Flight summary generation
- Battery voltage and current analysis
- GPS health monitoring
- Telemetry anomaly detection
- Cross-signal event correlation
- Time-window telemetry inspection
- Quaternion-to-Euler attitude conversion
- Motor output and saturation analysis
- Actual vs. commanded attitude comparison
- Vehicle velocity analysis
- Context-based event classification
- Unit testing with pytest

## Example: Investigating a Power Event

I tested NAVIS against a real PX4 ULog containing **75 logged telemetry topics**.

During the flight, the initial anomaly detector found two events at the same timestamp:

```text
Time:     70.22 s
Voltage:  17.94 V
Current:  48.83 A
```

The battery voltage dropped below the configured threshold at exactly the same time that current draw reached its maximum.

NAVIS correlated the two anomalies into a single power event.

At this point, simply labeling the event as a battery problem would have been premature. I added time-range inspection so NAVIS could examine the telemetry surrounding the event.

### Telemetry around 70.22 seconds

```text
Battery
Minimum Voltage       17.94 V
Maximum Current       48.83 A

GPS
Satellites            23–25

Actual Attitude
Maximum Roll          ~52.57°
Maximum Pitch         ~59.63°

Commanded Attitude
Maximum Roll          ~59.57°
Maximum Pitch         ~59.54°

Vehicle Motion
Horizontal Speed      27.08 m/s
Maximum Climb Rate     5.77 m/s

Motor Output
Motor 1 Max            1.000
Motor 2 Max            0.822
Motor 3 Max            1.000
Motor 4 Max            1.000
```

The additional telemetry changed the interpretation of the event.

Three motors reached normalized maximum output while the controller was commanding approximately 60 degrees of roll/pitch. The aircraft's actual attitude followed that command closely, horizontal velocity reached 27.08 m/s, and GPS remained healthy with 23–25 satellites.

Based on those signals, NAVIS classified the event as:

```text
Diagnosis:  HIGH LOAD MANEUVER
Confidence: HIGH
```

Rather than assuming the voltage sag represented an isolated battery fault, the analysis showed that it coincided with a high-demand maneuver.

This became an important design principle for the project:

> **An anomaly should be investigated in the context of the rest of the aircraft before it is treated as a fault.**

## Analysis Pipeline

NAVIS currently separates the analysis into several small tools.

### `list_flight_logs()`

Discovers supported flight log files in the configured data directory.

### `inspect_flight_log()`

Inspects a log and determines its format and available telemetry.

For PX4 ULogs, this includes discovering the logged uORB topics available for analysis.

### `flight_summary()`

Extracts high-level flight information such as:

- Flight duration
- Battery voltage
- Maximum altitude
- GPS satellite availability

### `detect_anomalies()`

Searches telemetry for conditions such as:

- Battery voltage sag
- High current draw
- Low GPS satellite count

### `correlate_anomalies()`

Checks whether anomalies occurred within the same time window and may represent a single event.

### `inspect_time_range()`

Examines telemetry around a selected point in the flight, including:

- Battery voltage and current
- GPS
- Altitude
- Vehicle attitude
- Motor outputs

### `diagnose_event()`

Adds flight context to a detected event by examining:

- Actual vehicle attitude
- Commanded attitude
- Horizontal velocity
- Climb/descent rate
- Motor saturation
- Battery behavior
- GPS health

The current diagnostic rules are deterministic and intentionally kept separate from the raw telemetry parser.

## Supported Formats

| Format | Platform / Source | Status |
| --- | --- | --- |
| `.ulg` | PX4 ULog | Supported |
| `.csv` | Generic telemetry | Basic support |
| `.bin` | ArduPilot DataFlash | Planned |
| `.tlog` | MAVLink telemetry | Planned |

A longer-term goal is to create a common telemetry representation so the analysis layer is not tightly coupled to one flight controller or log format.

## Tech Stack

- Python
- PyULog
- pytest
- Ollama
- Git / GitHub

## Project Structure

```text
NAVIS/
├── data/
│   └── sample flight data
├── tests/
│   └── test_tools.py
├── main.py
├── tools.py
├── requirements.txt
├── .gitignore
└── README.md
```

Large/raw flight logs used for development are excluded from the repository.

## Setup

Clone the repository:

```bash
git clone https://github.com/21YungK/NAVIS.git
cd NAVIS
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the test suite:

```bash
python -m pytest
```

## Roadmap

NAVIS is still under active development. Areas I plan to explore include:

- Additional PX4 anomaly detectors
- ArduPilot `.bin` support
- MAVLink `.tlog` support
- Common telemetry normalization
- Flight-to-flight comparison
- Battery and power-system analysis
- Automated investigation of detected events
- Telemetry visualization
- Flight-path visualization
- More realistic failure test cases
- Local model integration for natural-language flight analysis

## Status

**Work in progress!**

NAVIS is being developed incrementally, with each analysis capability tested against real or controlled flight-log data before expanding the diagnostic pipeline.
