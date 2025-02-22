# Axis Camera UI Application

A Python-based user interface (UI) application designed for Axis IP cameras, developed by **LiU TDDD96 Group 9** at Linköping University for the TDDD96 course. It integrates RTSP video streams, MQTT for real-time object detection data, and SQLite for persistent storage. The system automatically discovers Axis cameras on a network, aims to provide a UI for viewing live feeds with bounding boxes around detected objects, and saves frames with metadata to a database. **Note**: The UI component is still under development.

## Features
- **Camera Discovery**: Uses `ping` to detect devices, followed by RTSP checks to identify Axis cameras.
- **Live Streaming**: Displays RTSP feeds with real-time object detection overlays via OpenCV (UI in progress).
- **MQTT Integration**: Receives object detection data (e.g., humans, vehicles) from Axis cameras via MQTT.
- **Database Storage**: Saves video frames and detection metadata to a SQLite database.
- **Modular Design**: Organized into separate classes for broker management, database, MQTT client, RTSP streaming, and camera discovery.

## Prerequisites
- **Python**: 3.12 or higher
- **Dependencies**:
  - `opencv-python` (with FFmpeg support)
  - `paho-mqtt`
  - `numpy`
- **Mosquitto**: MQTT broker (installed and configured)
- **Network Access**: Axis cameras must be on the same network (e.g., `192.168.0.x` subnet).

## Installation
1. **Clone the Repository**:
   Clone the repository with `git clone <repository-url>` and navigate to the directory with `cd code`.

2. **Set Up a Virtual Environment** (optional but recommended):
   Create a virtual environment with `python -m venv venv` and activate it with `source venv/bin/activate` (on Windows: `venv\Scripts\activate`).

3. **Install Dependencies**:
   Install required packages with `pip install opencv-python paho-mqtt numpy`.

4. **Install Mosquitto**:
   - On Windows: Download from [Mosquitto website](https://mosquitto.org/download/) and install.
   - On Linux: Install with `sudo apt-get install mosquitto mosquitto-clients`.
   - Ensure a `mosquitto.conf` file exists in the project root or update `BrokerConfig` in `broker_manager.py` with the correct path.

5. **Verify FFmpeg**:
   - Ensure OpenCV is built with FFmpeg support by running this Python code: `import cv2; print(cv2.getBuildInformation())`. Look for `FFmpeg: YES`. If not, reinstall with `pip install opencv-python-headless[ffmpeg]`.

## Project Structure
- `code/`
  - `broker_manager.py` # Manages Mosquitto MQTT broker
  - `camera_discovery.py` # Discovers Axis cameras using ping and RTSP
  - `config.py` # RTSP configuration for Axis cameras
  - `database.py` # SQLite database management
  - `mqtt_client.py` # MQTT client for detection data
  - `rtsp_stream.py` # RTSP stream handling and display
  - `main.py` # Main application entry point
  - `.gitignore` # Git ignore file
  - `README.md` # This file
  - `LICENSE` # MIT License file

## Configuration
- **Camera Settings**: Update `RtspConfig` in `config.py` with your Axis camera’s username, password, and stream path if different from defaults (`student:student_pass`, `axis-media/media.amp`).
- **IP Range**: Adjust `base_ip`, `start_range`, and `end_range` in `CameraDiscovery` (`camera_discovery.py`) to match your network (default: `192.168.0.90-100`).
- **Database**: The SQLite database (`surveillance.db`) is created automatically with the schema for Axis camera data.

## Usage
1. **Run the Application**:
   Start the application with `python main.py`.

2. **What Happens**:
   - Starts the Mosquitto broker if not running.
   - Connects to MQTT for detection data from Axis cameras.
   - Loads existing cameras from the database (initially `192.168.0.93`).
   - Begins discovery to find new Axis cameras.
   - Opens windows showing live feeds with bounding boxes (UI development pending; currently uses OpenCV windows).

3. **Exit**:
   - Press `q` in any camera window to close it (main app continues until interrupted).
   - Use `Ctrl+C` in the terminal to shut down completely.

## Database Schema
The system uses SQLite to store:
- `Camera`: Camera details (ID, NAME, LOCATION, IP, RTSPURL)
- `Videoframe`: Saved frames (TIMESTAMP, TIMETOLIVE, FILEPATH, CAMERAID)
- `DetectedObject`: Objects in frames (GEOPOSITION, IMAGEVELOCITY, bounding box coordinates)
- Specialized tables: `Human`, `Vehicle`, etc., for object-specific data from Axis camera analytics.

## Troubleshooting
- **No Video Display**:
  - Check logs for H.264 errors (`Missing reference picture`, `decode_slice_header error`).
  - Test RTSP stream with `ffplay rtsp://student:student_pass@192.168.0.93:554/axis-media/media.amp`.
  - Ensure FFmpeg is enabled in OpenCV.

- **Slow Discovery**:
  - Verify ICMP (`ping`) isn’t blocked by your network; adjust `CameraDiscovery` to use TCP if needed.

- **MQTT Issues**:
  - Confirm Mosquitto is running and the Axis camera publishes to `axis/frame_metadata`.

## Current Limitations
- **UI Incomplete**: The graphical user interface is not yet implemented; currently uses OpenCV windows for display.
- **H.264 Decoding**: Occasional issues with decoding Axis camera streams (work in progress).
- **Single-threaded Streams**: May limit performance with multiple cameras (threading enhancements planned).

## License
This project is licensed under the MIT License by **LiU TDDD96 Group 9**. See the [`LICENSE`](LICENSE) file for details.