from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from app.heatmap.heatmap import create_heatmap
import os
import uuid
import logging
import logging

logger = logging.getLogger(__name__)

class Server:
    def __init__(self, mqtt_client, map_manager, alarm_manager):
        self.mqtt_client = mqtt_client
        self.map_manager = map_manager
        self.alarm_manager = alarm_manager

        
        self.app = Flask(__name__)
        logging.info(f"Starting Flask server...")
        CORS(self.app)
        self.ALARM_FILE = os.path.join("app", "alarms", "alarms.json")
        self.setup_routes()
        self.run()

    # close server when keyboard interrupt
    def __del__(self):
        logging.info("Stopping Flask server...")
        self.app.shutdown()
        logging.info("Flask server stopped.")

    def setup_routes(self):
        app = self.app

        @app.route("/api/alarms", methods=["POST"])
        def create_alarm_zone():
            new_alarm = request.get_json()
            if not new_alarm:
                return jsonify({"error": "No alarm zone provided"}), 400

            new_alarm["id"] = str(uuid.uuid4())
            self.alarm_manager.add_alarm(new_alarm)
            logging.info("Saved new alarm zone: %s", new_alarm)
            return (
                jsonify({"alarm": new_alarm, "message": "Alarm zone saved successfully"}),
                201,
            )

        @app.route("/api/alarms/<string:alarm_id>", methods=["DELETE"])
        def delete_alarm(alarm_id):
            self.alarm_manager.remove_alarm(alarm_id)
            logging.info("Removed alarm zone with id: %s", alarm_id)
            return jsonify({"message": "Alarm zone removed successfully"}), 200

        @app.route("/api/alarms", methods=["GET"])
        def get_alarms():
            alarms = self.alarm_manager.get_alarms_file()
            return jsonify({"alarms": alarms})
        
        @app.route("/api/alarms/status/<string:alarm_id>", methods=["POST", "PATCH"])
        def status_alarm(alarm_id):
            """
            POST endpoint for changing the status of an alarm zone by its ID.
            """
            success = self.alarm_manager.toggle_alarm(alarm_id)
            if not success:
                return jsonify({"error": "Alarm zone not found"}), 404
            return jsonify({"message": "Status changes succesfully"}), 200


        @app.route("/api/objects/<int:camera_id>", methods=["GET"])
        def get_camera_detections_by_id(camera_id: int):
            if not self.mqtt_client:
                return jsonify({"message": "MQTT client not available"}), 503
            raw = self.mqtt_client.object_manager.get_objects_by_camera(camera_id)
            observations = []
            for entry in raw:
                obj_id = entry.get("id")
                geo = entry.get("geoposition", {})
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat is None or lon is None:
                    continue
                x, y = self.map_manager.convert_to_relative((lat, lon))
                observations.append({"camera_id": camera_id, "x": x, "y": y, "id": obj_id})
            return jsonify({"observations": observations}), 200

        @app.route("/map")
        def get_map():
            if os.path.exists(self.map_manager.file_path):
                return send_file(self.map_manager.file_path)
            else:
                return jsonify({"message": "Map file not found"}), 404
            
        @app.route("/api/objects", methods=["GET"])
        def get_observations():
            """GET endpoint for retrieving all tracked observations in relative coords."""
            # retrieve raw position data from ObjectManager
            raw = self.mqtt_client.object_manager.get_all_objects()
            observations = []
            for entry in raw:
                cam_id = entry.get("camera_id")
                obj_id = entry.get("id")
                geo = entry.get("geoposition", {})
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat is None or lon is None:
                    continue
                x, y = self.map_manager.convert_to_relative((lat, lon))
                observations.append({"cid": cam_id, "x": x, "y": y, "id": obj_id})
            return jsonify({"objects": observations}), 200

        @app.route("/api/heatmap/<timeframe>", methods=["GET"])
        def get_heatmap(timeframe):
            payload = create_heatmap(timeframe, self.map_manager)
            return jsonify({"heatmap": payload}), 200


    def run(self):
        logging.info("Starting Flask server...")
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)  # Suppress Flask's default logging
        self.app.run(debug=True, port=5001, use_reloader=False, host="0.0.0.0")


if __name__ == "__main__":
    from app.mqtt.client import MqttClient
    from app.map.manager import MapManager

    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    floor_plan = os.path.join(assets_dir, "floor_plan.jpg")
    map_instance = MapManager(
        "Local House",
        [
            (59.3250, 18.0700),
            (59.3240, 18.0700),
            (59.3250, 18.0710),
            (59.3240, 18.0710),
        ],
        floor_plan,
        {
            1: (59.3249, 18.0701),
            2: (59.3242, 18.0709),
            3: (59.3245, 18.0705),
        },
    )

    mqtt_instance = MqttClient()
    mqtt_instance.connect()
    mqtt_instance.start_background_loop()

    server = Server(mqtt_instance, map_instance)
    server.run()
