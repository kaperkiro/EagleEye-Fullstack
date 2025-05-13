import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mqtt.broker import BrokerManager
from app.mqtt.client import MqttClient
from app.camera.webrtc import start_rtsp_to_webrtc
from app.server import Server
from app.camera.camera import Camera, clear_streams
from app.map.manager import MapManager
from app.map.map_config_gui import MapConfigGUI
from app.camera.arp_scan import scan_axis_cameras
from app.alarms.alarm import AlarmManager
from app.objects.manager import ObjectManager

import threading
import time
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Application:
    def __init__(self):
        self.running = True

        logger = logging.getLogger("Application")

        logger.info("Clearing RTSP to WebRTC config")
        clear_streams()

        logger.info("Scanning for cameras")
        self.cameras = self.find_cameras()

        logger.info("Checking for map config")
        self.map_config = self.load_map_config()

        logger.info("Updating camera configurations")
        self.update_cameras_configs()

        logger.info("Initializing map manager")
        self.map_manager = MapManager()

        logger.info("Initializing alarm manager")
        self.alarm_manager = AlarmManager()
        
        logger.info("Initializing object manager")
        self.object_manager = ObjectManager(self.map_manager, self.alarm_manager)

        logger.info("Initializing MQTT broker")
        self.broker = BrokerManager()

        logger.info("Initializing MQTT client")
        self.mqtt_client = MqttClient(self.object_manager)

        logger.info("Starting RTSP to WebRTC server")
        threading.Thread(target=start_rtsp_to_webrtc, daemon=True).start()

        logger.info("Starting Flask server")
        threading.Thread(target=Server, args=(self.mqtt_client, self.map_manager, self.alarm_manager), daemon=True).start()

    def find_cameras(self):
        cameras = []
        try:
            scan_results = scan_axis_cameras()
            if scan_results:
                for id, ip, mac, manufacturer in scan_results:
                    cameras.append(Camera(ip=ip, id=id))
                return cameras
            else:
                logger.info("No Axis cameras found on 192.168.0.0/24 subnet")
                return []
        except Exception as e:
            logger.error(f"Error during camera discovery: {str(e)}")
    
    def load_map_config(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map", "map_config.json")
            if os.path.exists(path):
                with open(path, "r") as json_file:
                    return json.load(json_file)
                logger.info("Map config loaded from file")
            else:
                logger.info("Map config file not found, creating new one")
                MapConfigGUI() # Open the GUI to create a new map config
                with open(path, "r") as json_file:
                    return json.load(json_file)
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

    def stop_application(self):
        self.running = False
        self.mqtt_client.stop()
        self.broker.stop()
        logger.info("Application stopped")

    def run(self):
        try:
            while self.running:
                time.sleep(1)

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
        finally:
            logger.info("Stopping application")
            self.stop_application()

def main():
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
