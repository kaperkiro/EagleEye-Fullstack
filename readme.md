# EagleEye Surveillance System

EagleEye is a real-time surveillance and monitoring system designed to detect, track, and visualize human activity in defined areas using Axis cameras. The system is split into two main components:

- **Backend**  
  A Flask-based REST API that:

  - Processes video feeds from cameras.
  - Performs real-time object detection and object tracking.
  - Generates heatmaps from accumulated observation data.
  - Manages alarms triggered upon restricted area violations.
  - Communicates via MQTT for real-time data exchange.

- **Frontend**  
  A React and TypeScript application that:
  - Displays a live video view.
  - Renders historical heatmaps.
  - Manages and displays alarm zones.

## Architecture Overview

The system is designed using a modular architecture with the components outlined below:

- **Camera Module**: Configures and processes video feeds, detects objects, and forwards observations.
- **MQTT Communication**: Publishes and subscribes to topics to pass data in real time.
- **Object Tracking**: Aggregates and verifies observations across cameras.
- **Map Management**: Converts real-world coordinates to relative positions on floor plans.
- **Heatmap Generation**: Creates a normalized heatmap overlay based on sensor data.
- **Alarm System**: Monitors restricted zones and triggers notifications.
- **Web Server**: A Flask server exposing the REST API endpoints for alarms, objects, heatmaps, and camera positions.
- **Frontend**: React views that offer live viewing, historical heatmap visualization, and alarm management interfaces.

## Requirements

- **Backend**

  - Python 3.8 or higher
  - Go (for RTSP-to-WebRTC conversion; see [Go Downloads](https://go.dev/dl/))
  - Mosquitto MQTT Broker
  - Dependencies listed in the [`requirements.txt`](./backend/requirements.txt)

- **Frontend**
  - Node.js (v18+ recommended)
  - npm

## Installation

1. **Clone the Repository**

   ```bash
   git clone <repository_url>
   cd EagleEye-Fullstack
   ```

2. **Setup Backend**

   - Navigate to the backend directory and install Python dependencies:
     ```bash
     cd backend
     pip install -r requirements.txt
     ```
   - Ensure Go is installed and added to your PATH.
   - Install and configure the Mosquitto MQTT Broker.

3. **Setup Frontend**
   - Navigate to the React frontend directory and install dependencies:
     ```bash
     cd frontend/react-frontend
     npm install
     ```

## Running the Project

You can run the entire system using the provided orchestration script (`run.py`):

- **Using the Run Script:**

  ```bash
  python run.py
  ```

  This script starts the backend (Flask server) and the frontend development server (using Vite) concurrently.

  - **Or try docker:**

  ```bash
  docker-compose up --build

  ```

- **Running Separately:**

  - **Backend:**

    ```bash
    cd backend/Backend-Code/app
    python main.py
    ```

    _Note: Administrative privileges may be required for ARP scanning._

  - **Frontend:**
    ```bash
    cd frontend/react-frontend
    npm run dev
    ```
    Default access will available at [http://localhost:5173](http://localhost:5173).
