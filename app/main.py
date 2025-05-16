import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mqtt.broker import BrokerManager
from app.mqtt.client import MqttClient
from app.camera.webrtc import start_rtsp_to_webrtc, clear_streams
from app.server import Server
from app.map.manager import MapManager
from app.camera.arp_scan import find_cameras
from app.alarms.alarm import AlarmManager
from app.objects.manager import ObjectManager

import threading
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s - %(message)s")

class Application:
    def __init__(self):
        self.running = True

        logger = logging.getLogger("Application")

        logger.info("Clearing RTSP to WebRTC config")
        clear_streams()

        logger.info("Scanning for cameras")
        self.cameras = find_cameras()

        logger.info("Initializing map manager")
        self.map_manager = MapManager()

        logger.info("Checking for map config")
        self.map_config = self.map_manager.load_map_config()

        logger.info("Updating camera configurations")
        self.update_cameras_configs()

        logger.info("Initializing alarm manager")
        self.alarm_manager = AlarmManager()
        
        logger.info("Initializing object manager")
        self.object_manager = ObjectManager(self.map_manager, self.alarm_manager)

        logger.info("Initializing MQTT broker")
        self.broker = BrokerManager()

        logger.info("Initializing MQTT client")
        self.mqtt_client = MqttClient(self.object_manager)

        self.webrtc_thread = threading.Thread(target=start_rtsp_to_webrtc, daemon=True)
        self.webrtc_thread.start()

        self.server_thread = threading.Thread(target=Server, args=(self.mqtt_client, self.map_manager, self.alarm_manager), daemon=True)
        self.server_thread.start()

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

    def run(self):
        try:
            while self.running:
                pass

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            self.stop_application()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping application, please wait...")
            self.stop_application()
        except SystemExit:
            logger.info("System exit received, stopping application, please wait...")
            self.stop_application()
        except BaseException as e:
            logger.error(f"Unexpected error: {str(e)}")
            self.stop_application()
        except:
            logger.error("An unknown error occurred!")
            self.stop_application()
        finally:
            self.stop_application()

def main():
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
