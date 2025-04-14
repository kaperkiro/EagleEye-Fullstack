from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import json
import logging

# Import your MqttClient class
from mqtt_client import MqttClient

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)

ALARM_FILE = "alarms.json"
MAP_PATH = "map.jpg"

global mqtt_client
mqtt_client = None


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


@app.route("/api/alarms/<string:alarm_id>", methods=["DELETE"])
def delete_alarm(alarm_id):
    alarms = load_alarms()
    new_alarms = [alarm for alarm in alarms if alarm.get("id") != alarm_id]
    if len(new_alarms) == len(alarms):
        return jsonify({"error": "No matching alarm zone found"}), 404
    save_alarms(new_alarms)
    logging.info("Removed alarm zone with id: %s", alarm_id)
    return jsonify({"message": "Alarm zone removed successfully"}), 200


@app.route("/api/alarms/status/<string:alarm_id>", methods=["POST"])
def status_alarm(alarm_id):
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
    alarms = load_alarms()
    logging.info(f"Loaded {len(alarms)} alarm zones.")
    return jsonify({"alarms": alarms})


@app.route("/api/detections/<int:camera_id>", methods=["GET"])
def get_camera_detections(camera_id):
    if mqtt_client:
        detections = mqtt_client.get_detections(camera_id)
        position = mqtt_client.position
        logging.info(
            f"API request for positions from camera {camera_id}, found {len(position)} detections."
        )
        return jsonify(
            {"camera_id": camera_id, "detections": detections, "position": position}
        )
    else:
        logging.warning(
            f"API request for detections from camera {camera_id}, but MQTT client is not initialized."
        )
        return jsonify({"message": "MQTT client not available"}), 503


@app.route("/map")
def get_map():
    if os.path.exists(MAP_PATH):
        return send_file(MAP_PATH, mimetype="image/jpeg")
    else:
        return jsonify({"message": "Map file not found"}), 404


def run_flask_server(mqtt_client_instance: MqttClient):
    global mqtt_client
    mqtt_client = mqtt_client_instance
    logging.info("Starting Flask server...")
    app.run(debug=True, port=5001, use_reloader=False, host="0.0.0.0")


if __name__ == "__main__":
    run_flask_server(MqttClient())
