from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import json
import logging
import threading
from MqttPublisher.mqtt_pub import MqttPublisher
import heatmap

# Removed invalid import statement. If 'map' is a custom module, use 'import map'.

# Import your MqttClient class
from mqtt_client import MqttClient
from map_manager import MapManager

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)

ALARM_FILE = "alarms.json"
MAP_PATH = "map.jpg"

global mqtt_client
mqtt_client = None

global map_manager
map_manager = None


def load_alarms():
    if os.path.exists(ALARM_FILE):
        try:
            with open(ALARM_FILE, "r") as f:
                alarms = json.load(f)
                if isinstance(alarms, list):
                    return alarms
        except Exception as e:
            logging.error(f"Error reading alarms file: {e}")
    return []


def save_alarms(alarms):
    try:
        with open(ALARM_FILE, "w") as f:
            json.dump(alarms, f)
    except Exception as e:
        logging.error(f"Error writing alarms file: {e}")


@app.route("/api/alarms", methods=["POST"])
def create_alarm_zone():
    """
    POST endpoint for creating a new alarm zone.
    Expects JSON with the alarm zone properties (excluding the id), e.g.:
    {
         "topLeft": {"x": number, "y": number},
         "bottomRight": {"x": number, "y": number},
         "active": <boolean>,
         "triggered": <boolean>
    }
    The backend will generate a unique ID for the alarm zone.
    """
    new_alarm = request.get_json()
    if not new_alarm:
        return jsonify({"error": "No alarm zone provided"}), 400

    # Generate a unique ID for the new alarm zone using uuid4
    new_alarm["id"] = str(uuid.uuid4())

    alarms = load_alarms()
    alarms.append(new_alarm)
    save_alarms(alarms)
    logging.info("Saved new alarm zone: %s", new_alarm)
    return (
        jsonify({"alarm": new_alarm, "message": "Alarm zone saved successfully"}),
        201,
    )


@app.route("/api/heatmap/<timeframe>", methods=["GET"])
def get_heatmap(timeframe):
    payload = heatmap.create_heatmap(timeframe, map_instance)
    return jsonify({"heatmap": payload}), 200


@app.route("/api/alarms/<string:alarm_id>", methods=["DELETE"])
def delete_alarm(alarm_id):
    """
    DELETE endpoint for removing an alarm zone by its ID.

    """
    alarms = load_alarms()
    new_alarms = [alarm for alarm in alarms if alarm.get("id") != alarm_id]
    if len(new_alarms) == len(alarms):
        return jsonify({"error": "No matching alarm zone found"}), 404
    save_alarms(new_alarms)
    logging.info("Removed alarm zone with id: %s", alarm_id)
    return jsonify({"message": "Alarm zone removed successfully"}), 200


@app.route("/api/alarms/status/<string:alarm_id>", methods=["POST", "PATCH"])
def status_alarm(alarm_id):
    """
    POST endpoint for changing the status of an alarm zone by its ID.
    """
    if not alarm_id:
        return jsonify({"message": "No zone included "}), 404
    alarms = load_alarms()
    for alarm in alarms:
        if alarm["id"] == alarm_id:
            alarm["active"] = not alarm["active"]
            save_alarms(alarms)
            return jsonify({"message": "Status changes succesfully"}), 200
    return jsonify({"message": "Zone not found "}), 404


@app.route("/api/alarms", methods=["GET"])
def get_alarms():
    """
    GET endpoint for retrieving all alarm zones.
    """
    alarms = load_alarms()
    logging.info(f"Loaded {len(alarms)} alarm zones.")
    return jsonify({"alarms": alarms})


@app.route("/api/objects/<int:camera_id>", methods=["GET"])
def get_camera_detections_by_id(camera_id: int) -> jsonify:
    """Gets all tracked detections for a camera in relative coords."""
    # Ensure MQTT client is initialized
    if not mqtt_client:
        return jsonify({"message": "MQTT client not available"}), 503
    # Get global object list for this camera
    raw = mqtt_client.object_manager.get_objects_by_camera(camera_id)
    observations = []
    for entry in raw:
        obj_id = entry.get("id")
        geo = entry.get("geoposition", {})
        lat = geo.get("latitude")
        lon = geo.get("longitude")
        if lat is None or lon is None:
            continue
        x, y = map_manager.convert_to_relative((lat, lon))
        observations.append({"camera_id": camera_id, "x": x, "y": y, "id": obj_id})
    return jsonify({"observations": observations}), 200


@app.route("/api/objects", methods=["GET"])
def get_observations():
    """GET endpoint for retrieving all tracked observations in relative coords."""
    if mqtt_client:
        # retrieve raw position data from ObjectManager
        raw = mqtt_client.object_manager.get_all_objects()
        observations = []
        for entry in raw:
            cam_id = entry.get("camera_id")
            obj_id = entry.get("id")
            geo = entry.get("geoposition", {})
            lat = geo.get("latitude")
            lon = geo.get("longitude")
            if lat is None or lon is None:
                continue
            x, y = map_manager.convert_to_relative((lat, lon))
            observations.append({"cid": cam_id, "x": x, "y": y, "id": obj_id})
        return jsonify({"objects": observations}), 200
    else:
        return jsonify({"message": "MQTT client not available"}), 503


@app.route("/test", methods=["GET"])
def test() -> jsonify:
    """Test endpoint to check if the server is running and to get a test detection.
    Returns:
        jsonify: _jsonify with a test detection. Use this with the mock mqtt_pub.py
    """

    num = 1
    print(f"API request for test from camera {num}")
    if mqtt_client:
        if mqtt_client.position:
            x, y = map_manager.convert_to_relative(mqtt_client.position[0])
            position = [1, x, y]
            detections = mqtt_client.get_detections(num)
            return jsonify({"position": position})
        else:
            return jsonify({"message": "No position data available"}), 503


@app.route("/map")
def get_map():
    """
    This endpoint is used to send the map file to the client.
    """
    print("Sending map file")
    if os.path.exists(map_manager.file_path):
        return send_file(map_manager.file_path)
    else:
        return jsonify({"message": "Map file not found"}), 404


@app.route("/api/camera_positions", methods=["GET"])
def get_camera_positions():
    """Returns the camera positions in relative coordinates."""
    if mqtt_client:
        camera_positions = map_manager.camera_relative_coords
        if not camera_positions:
            return jsonify({"message": "No camera positions available"}), 503
        return jsonify({"cam_pos": camera_positions}), 200
    else:
        return jsonify({"message": "MQTT client not available"}), 503


def run_flask_server(
    mqtt_client_instance: MqttClient, map_manager_instance: MapManager
):
    global mqtt_client
    mqtt_client = mqtt_client_instance
    global map_manager
    map_manager = map_manager_instance
    logging.info("Starting Flask server...")
    app.run(debug=True, port=5001, use_reloader=False, host="0.0.0.0")


if __name__ == "__main__":
    # Initialize the map holder
    map_instance = MapManager(
        "Local House",
        [
            (59.3250, 18.0700),
            (59.3240, 18.0700),
            (59.3250, 18.0710),
            (59.3240, 18.0710),
        ],
        "assets/floor_plan.jpg",
        {
            1: (59.3250, 18.0701),  # top-left
            2: (59.3241, 18.0710),  # bottom-right
            3: (59.3245, 18.0705),  # center
        },
    )

    mqtt_instance = MqttClient()
    mqtt_instance.connect()
    mqtt_instance.start_background_loop()

    # Start dummy publisher for integrated testing
    publisher = MqttPublisher()
    publisher.connect()
    threading.Thread(target=publisher.run, daemon=True).start()

    publisher = MqttPublisher(camera_id=100)
    publisher.connect()
    threading.Thread(target=publisher.run, daemon=True).start()

    run_flask_server(mqtt_instance, map_instance)
