# EagleEye Surveillance System

## Overview

EagleEye is a real-time surveillance and monitoring system designed to detect, track, and visualize human activity within a defined area using Axis cameras. The system processes video feeds, performs object detection (humans), tracks objects across multiple cameras, generates heatmaps of activity, and triggers alarms for restricted area violations with email notifications. It leverages MQTT for communication, a Flask-based web API for data access, a graphical interface for map configuration, and a modular architecture for scalability.

Key features include:
- **Object Detection and Tracking**: Detects humans and faces in camera feeds, tracks them across multiple cameras using geoposition data.
- **Heatmap Generation**: Visualizes activity density on a 20×20 grid overlaid on a floor plan.
- **Alarm System**: Triggers email alerts when objects enter predefined restricted areas.
- **Map Configuration**: Provides a Tkinter-based GUI to configure the floor plan and camera positions.
- **MQTT Communication**: Publishes and subscribes to observation data for real-time processing.
- **Web API**: Serves object positions, heatmaps, camera positions, and floor plans via Flask endpoints.
- **Simulated Data**: Supports dummy data generation for testing and development.
- **Custom Logging**: Logs events with colored console output and persistent file logging.

## Project Structure

The project is organized into several directories, each handling specific functionality:

```
root/
├── app/
│   ├── alarms/              # Alarm management for restricted areas
│   │   ├── alarm.py
│   │   ├── mail_sender.py
│   │   └── alarms.json
│   ├── camera/              # Camera configuration and video processing
│   │   ├── arp_scan.py
│   │   ├── cameras.json
│   │   ├── camera.py
│   │   └── webrtc.py
│   ├── heatmap/             # Heatmap generation
│   │   ├── heatmap.py
│   │   └── heatmap_data.json
│   ├── map/                 # Map and geoposition management
│   │   ├── manager.py
│   │   ├── map_config.json
│   │   └── map_config_gui.py
│   ├── mqtt/                # MQTT communication
│   │   ├── broker.py
│   │   ├── client.py
│   │   └── publisher.py
│   ├── objects/             # Global object tracking
│   │   └── manager.py
│   ├── assets/              # Static assets (e.g., floor plan image)
│   │   ├── floor_plan.png
│   │   └── floor_plan.jpg
│   ├── logger.py            # Custom logging setup
│   ├── main.py              # Application entry point
│   └── server.py            # Flask server for API endpoints
├── external/
│   ├── RTSPtoWebRTC/        # External RTSP to WebRTC conversion tools
│   └── mosquitto.conf       # Mosquitto MQTT broker configuration
└── requirements.txt         # Python dependencies
```

## Architecture

EagleEye operates as a modular system with the following components:

1. **Camera Module (`app/camera/`)**:
   - Configures Axis cameras (`cameras.json`) and processes video feeds (`camera.py`, `webrtc.py`).
   - Discovers cameras via ARP scan (`arp_scan.py`).
   - Outputs observations (humans/faces with bounding boxes, geopositions, timestamps).

2. **MQTT Communication (`app/mqtt/`)**:
   - **Broker (`broker.py`)**: Manages the Mosquitto MQTT broker for message passing.
   - **Publisher (`publisher.py`)**: Simulates human movement by publishing dummy observations to MQTT topics (`{camera_id}/frame_metadata`).
   - **Client (`client.py`)**: Subscribes to MQTT topics, receives observations, and forwards them to the object manager.

3. **Object Tracking (`app/objects/`)**:
   - `manager.py`: Tracks objects globally across cameras using `GlobalObject` and `ObjectManager` classes.
   - Matches observations based on geoposition proximity (within 1 meter) using `ObjectManager.check_if_same_observation`.
   - Archives objects no longer in view and buffers observations to `heatmap_data.json` with batch writing (100 observations or 5 seconds).

4. **Map Management (`app/map/`)**:
   - `manager.py`: Converts geocoordinates to relative coordinates (u%, v%) for mapping onto a floor plan.
   - `map_config_gui.py`: Provides a Tkinter-based GUI to configure the floor plan, room corners, and camera positions.
   - `map_config.json`: Stores map metadata, including corner geocoordinates and camera positions.

5. **Heatmap Generation (`app/heatmap/`)**:
   - `heatmap.py`: Generates a 20×20 grid heatmap from observations in `heatmap_data.json`, normalized by the busiest cell.
   - Outputs data in the format `{ "last_{timeframe_min}_min": [{ "x": float, "y": float, "intensity": float }, ...] }`.

6. **Alarm System (`app/alarms/`)**:
   - `alarm.py`: Checks if objects enter restricted areas defined in `alarms.json`.
   - Triggers email alerts via `mail_sender.py` with a hardcoded receiver email.

7. **Web Server (`app/server.py`)**:
   - Runs a Flask server on port 5001, providing API endpoints for alarms, objects, heatmaps, camera positions, and floor plans.
   - Integrates with `MapManager`, `AlarmManager`, and `ObjectManager` for data retrieval.

8. **Logging (`app/logger.py`)**:
   - Implements a custom logger with colored console output and file logging to `eagleeye.log`.

9. **Application (`app/main.py`)**:
   - Orchestrates all components, running MQTT, WebRTC, and the Flask server in separate threads.
   - Handles graceful shutdown on `KeyboardInterrupt`.

10. **External RTSP to WebRTC (`external/RTSPtoWebRTC/`)**:
    - Contains tools or scripts for converting RTSP streams from Axis cameras to WebRTC for streaming, integrated via `app/camera/webrtc.py`.

## Prerequisites

- **Python 3.8+**
- **Go**: Required for RTSPtoWebRTC. Install the latest version from the official Go website (https://go.dev/dl/).
- **Mosquitto MQTT Broker**: Required for MQTT communication.
- **Axis Cameras**: Configured with accessible IP addresses (or use dummy data for testing).
- **Dependencies**:
  See `requirements.txt` for a complete list.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://gitlab.liu.se/tddd96-pum09/Backend-Code.git
   cd Backend-Code
   ```

2. **Install Go**:
   - Download and install Go from https://go.dev/dl/ (e.g., for Linux: `go1.22.2.linux-amd64.tar.gz` as of May 23, 2025).
   - Extract and install:
     ```bash
     tar -C /usr/local -xzf go1.22.2.linux-amd64.tar.gz
     export PATH=$PATH:/usr/local/go/bin
     ```
   - Verify installation:
     ```bash
     go version
     ```
   - Add Go to your PATH permanently by adding `export PATH=$PATH:/usr/local/go/bin` to your `~/.bashrc` or `~/.zshrc` and run `source ~/.bashrc`.

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Mosquitto**:
   - On Ubuntu:
     ```bash
     sudo apt-get install mosquitto mosquitto-clients
     ```
   - On macOS:
     ```bash
     brew install mosquitto
     ```
   - Verify Mosquitto installation:
     ```bash
     mosquitto -h
     ```
   - If not recognized, set system variables or specify the full path to the Mosquitto executable.

5. **Configure Settings**:
   - Place the floor plan image (e.g., `floor_plan.jpg` or `floor_plan.png`) in `app/assets/`.
   - Update the receiver email for alarm notifications directly in `app/alarms/mail_sender.py`.

## Usage

1. **Run the Application**:
   ```bash
   sudo python3 app/main.py
   ```
   Note: Admin privilege needed for arp scan.

## API Endpoints

The Flask server provides the following endpoints:

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/alarms` | GET | List all alarm zones | None |
| `/api/alarms` | POST | Create a new alarm zone | JSON body with alarm details |
| `/api/alarms/<alarm_id>` | DELETE | Remove an alarm zone | `alarm_id` (string) |
| `/api/alarms/status/<alarm_id>` | POST, PATCH | Toggle alarm status | `alarm_id` (string) |
| `/api/objects/<camera_id>` | GET | Get objects for a specific camera | `camera_id` (integer) |
| `/api/objects` | GET | Get all tracked objects | None |
| `/api/heatmap/<timeframe>` | GET | Generate heatmap for a timeframe | `timeframe` (integer, seconds) |
| `/api/camera_positions` | GET | Get camera positions | None |
| `/map` | GET | Serve floor plan image | None |

**Example Response** (GET `/api/objects`):
```json
{
  "objects": [
    {"cid": 1, "x": 10.5, "y": 20.3, "id": "uuid-1234"},
    {"cid": 2, "x": 15.2, "y": 25.7, "id": "uuid-5678"}
  ]
}
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, contact the project maintainers at `pumgrupp9-users@liuonline.onmicrosoft.com`.