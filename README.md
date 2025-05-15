# EagleEye Surveillance System

## Overview

EagleEye is a real-time surveillance and monitoring system designed to detect, track, and visualize human activity within a defined area using Axis cameras. The system processes video feeds, performs object detection (humans and faces), tracks objects across multiple cameras, generates heatmaps of activity, and triggers alarms for restricted area violations. It leverages MQTT for communication, a graphical interface for map configuration, and a modular architecture for scalability.

Key features include:
- **Object Detection and Tracking**: Detects humans and faces in camera feeds, tracks them across multiple cameras using geoposition data.
- **Heatmap Generation**: Visualizes activity density on a 20×20 grid overlaid on a floor plan.
- **Alarm System**: Triggers alerts when objects enter predefined restricted areas.
- **Map Configuration**: Provides a GUI to configure the floor plan and camera positions.
- **MQTT Communication**: Publishes and subscribes to observation data for real-time processing.
- **Simulated Data**: Supports dummy data generation for testing and development.

## Project Structure

The project is organized into several directories, each handling specific functionality:

```
root/
├── app/
│   ├── alarms/              # Alarm management for restricted areas
│   │   ├── alarm.py
│   │   └── alarms.json
│   ├── camera/              # Camera configuration and video processing
│   │   ├── cameras.json
│   │   ├── calibration.py
│   │   ├── camera.py
│   │   └── webrtc.py
│   ├── heatmap/             # Heatmap generation
│   │   ├── heatmap.py
│   │   └── heatmap_data.jl
│   ├── helper/              # Utility functions
│   │   └── helper.py
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
│   └── assets/              # Static assets (e.g., floor plan image)
│       ├── floor_plan.png
│       └── floor_plan.jpg
├── external/
│   └── mosquitto.conf       # Mosquitto MQTT broker configuration
```

## Architecture

EagleEye operates as a modular system with the following components:

1. **Camera Module (`app/camera/`)**:
   - Configures Axis cameras (`cameras.json`) and processes video feeds (`camera.py`, `webrtc.py`).
   - Uses calibration data (`calibration.py`) to map camera coordinates to geopositions.
   - Outputs observations (humans/faces with bounding boxes, geopositions, timestamps).

2. **MQTT Communication (`app/mqtt/`)**:
   - **Broker (`broker.py`)**: Manages the Mosquitto MQTT broker for message passing.
   - **Publisher (`publisher.py`)**: Simulates human movement by publishing dummy observations to MQTT topics (`{camera_id}/frame_metadata`).
   - **Client (`client.py`)**: Subscribes to MQTT topics, receives observations, and forwards them to the object manager.

3. **Object Tracking (`app/objects/`)**:
   - `manager.py`: Tracks objects globally across cameras using `GlobalObject` and `ObjectManager` classes.
   - Matches observations based on geoposition proximity and clothing colors (`helper.py`).
   - Archives objects no longer in view and saves observations to `heatmap_data.jl`.

4. **Map Management (`app/map/`)**:
   - `manager.py`: Converts geocoordinates to relative coordinates (u%, v%) for mapping onto a floor plan.
   - `map_config_gui.py`: Provides a Tkinter-based GUI to configure the floor plan, room corners, and camera positions.
   - `map_config.json`: Stores map metadata, including corner geocoordinates and camera positions.

5. **Heatmap Generation (`app/heatmap/`)**:
   - `heatmap.py`: Generates a 20×20 grid heatmap from observations in `heatmap_data.jl`, normalized by the busiest cell.
   - Outputs data in the format `{ "last_{timeframe_min}_min": [{ "x": float, "y": float, "intensity": float }, ...] }`.

6. **Alarm System (`app/alarms/`)**:
   - `alarm.py`: Checks if objects enter restricted areas defined in `alarms.json`.
   - Triggers alerts based on relative coordinates from the map manager.

7. **Utilities (`app/helper/`)**:
   - `helper.py`: Contains `check_if_same_observation` to compare observations based on geoposition (within 1.5m) and clothing colors.

## Prerequisites

- **Python 3.8+**
- **Mosquitto MQTT Broker**: Install Mosquitto for MQTT communication.
- **Axis Cameras**: Configured with accessible IP addresses (or use dummy data for testing).
- **Dependencies**:
  See requirements.txt

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://gitlab.liu.se/tddd96-pum09/Backend-Code.git
   cd Backend-Code
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Mosquitto**:
   - On Ubuntu:
     ```bash
     sudo apt-get install mosquitto mosquitto-clients
     ```
   - On macOS:
     ```bash
     brew install mosquitto
     ```
   - Ensure the `mosquitto.conf` file is placed in the `external/` directory and that mosquitto is properly configured on your computer by entering the following in your terminal:
     ```bash
     mosquitto -h
     ```
   - If mosquitto is not recognized you might have to correctly set your system variables.
     
4. **Run main.py**:
   - Run the program with the following command.
     ```bash
     python3 app/main.py
     ```

## Notes

- **Performance**: The system assumes a small number of cameras. For large setups, optimize MQTT message handling and object tracking.
- **Security**: Secure the MQTT broker with authentication in production environments.
- **Frontend**: To be implemented in the same git repository.


## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, contact the project maintainers at pumgrupp9-users@liuonline.onmicrosoft.com.