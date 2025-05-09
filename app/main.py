import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mqtt.broker import BrokerManager
from app.mqtt.client import MqttClient
from app.camera.webrtc import start_rtsp_to_webrtc
from app.server import run_flask_server
from app.camera.camera import Camera, clear_streams
from app.map.manager import MapManager
from app.map.map_config_gui import MapConfigGUI
from app.camera.arp_scan import scan_axis_cameras

import threading
import time
import logging
import json

logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        self.broker = BrokerManager()
        self.mqtt_client = MqttClient()
        self.running = True
        self.cameras = []
        self.map_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map", "map_config.json")

    def find_cameras(self):
        try:
            scan_results = scan_axis_cameras()
            if not scan_results: # För att hitta när man kör via routern
                logger.info("No Axis cameras found at 192.168.0.0/24 trying 192.168.1.0/24")
                scan_results = scan_axis_cameras(ip_range="192.168.1.0/24")
            if scan_results:
                for id, ip, mac, manufacturer in scan_results:
                    self.cameras.append(Camera(ip=ip, id=id))
            else:
                logger.info("No Axis cameras found")
        except Exception as e:
            logger.error(f"Error during camera discovery: {str(e)}")
    
    def load_map_config(self):
        try:
            if os.path.exists(self.map_config):
                with open(self.map_config, "r") as json_file:
                    self.map_config = json.load(json_file)
                logger.info("Map config loaded from file")
            else:
                logger.info("Map config file not found, creating new one")
                MapConfigGUI()
                with open(self.map_config, "r") as json_file:
                    self.map_config = json.load(json_file)
        except Exception as e:
            logger.error(f"Error loading map config: {str(e)}")

    def update_cameras_configs(self):
        try:
            for camera in self.cameras:
                if str(camera.id) in self.map_config["cameras"]:
                    cam_settings = self.map_config["cameras"][str(camera.id)]
                    lat = cam_settings["geocoordinates"][0]
                    lon = cam_settings["geocoordinates"][1]
                    height = cam_settings["height"]
                    heading = cam_settings["heading"]
                    camera.configure_camera(lat, lon, height, heading)
        except Exception as e:
            logger.error(f"Error updating camera configurations: {str(e)}")

    def run(self):
        try:
            # Clear all streams from config.json
            clear_streams()

            logger.info("Scanning for cameras")
            self.find_cameras()

            logger.info("Starting MQTT broker")
            self.broker.start()

            logger.info("Connecting MQTT client")
            self.mqtt_client.start()

            logger.info("Checking for map config")
            self.load_map_config()            
                
            map_hol = MapManager()

            logger.info("Updating camera configurations")
            self.update_cameras_configs()

            logger.info("Starting RTSP to WebRTC server")
            threading.Thread(target=start_rtsp_to_webrtc, daemon=True).start()

            logger.info("Starting Flask server")
            threading.Thread(
                target=run_flask_server, args=(self.mqtt_client, map_hol), daemon=True
            ).start()

            while self.running:
                time.sleep(1)

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
        finally:
            self.running = False
            self.mqtt_client.stop()
            self.broker.stop()
            logger.info("Application shutdown complete")

def main():
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
