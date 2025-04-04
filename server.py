from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
# Importera dina andra moduler vid behov
# from database import Database 
import base64
import os
# import sqlite3 # Importera om du använder det direkt
import atexit # För att städa upp vid avslut
import logging

# Importera din MqttClient-klass
from mqtt_client import MqttClient 

logging.basicConfig(level=logging.INFO) # Konfigurera logging för servern

app = Flask(__name__)
CORS(app)
# db = Database() # Initiera databas om den används
MAP_PATH = "map.jpg"

# ---- MQTT Klient Instans ----
# Skapa en global variabel för att hålla MQTT-klienten
# Den kommer att initieras när skriptet körs direkt (__name__ == "__main__")
global mqtt_client
mqtt_client = None


# ---- API Routes ----


@app.route("/api/detections/<int:camera_id>", methods=["GET"])
def get_camera_detections(camera_id):
    """
    API endpoint för att hämta de senaste detektionerna för en specifik kamera.
    """
    if mqtt_client:
        detections = mqtt_client.get_detections(camera_id)

        position = mqtt_client.position


        logging.info(f"API request for positions from camera {camera_id}, found {len(position)} detections.")
        return jsonify({
            "camera_id": camera_id,
            "detections": detections,
            "position" : position
        })
    else:
        logging.warning(f"API request for detections from camera {camera_id}, but MQTT client is not initialized.")
        # Returnera 503 Service Unavailable om klienten inte är redo
        return jsonify({"message": "MQTT client not available"}), 503 

@app.route("/map")
def get_map():
    if os.path.exists(MAP_PATH):
        return send_file(MAP_PATH, mimetype='image/jpeg')
    else:
         return jsonify({"message": "Map file not found"}), 404
    




def run_flask_server(mqtt_client_instance: MqttClient):
    """
    Startar Flask-servern med den givna MQTT-klienten.
    :param mqtt_client_instance: Instans av MqttClient som ska användas.
    """
    global mqtt_client
    # Sätt den globala MQTT-klienten till den som skickades in
    # i funktionen så att den kan användas i API-rutterna
    mqtt_client = mqtt_client_instance 
    """
    Startar Flask-servern.
    """
    logging.info("Starting Flask server...")
    app.run(debug=True, port=5001, use_reloader=False, host='0.0.0.0')
