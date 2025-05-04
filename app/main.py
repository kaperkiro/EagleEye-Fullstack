import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mqtt.broker import BrokerManager
from app.mqtt.client import MqttClient
from app.camera.webrtc import start_rtsp_to_webrtc
from app.server import run_flask_server
import threading
import time
import logging
from app.camera.camera import Camera, clear_streams
from app.map.manager import MapManager
from app.camera.arp_scan import scan_axis_cameras

logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.broker = BrokerManager()
        self.mqtt_client = MqttClient()
        self.running = True
        self.cameras = []

    def find_cameras(self):
        try:
            scan_results = scan_axis_cameras()
            if scan_results:
                for id, ip, mac, manufacturer in scan_results:
                    self.cameras.append(Camera(ip=ip, id=id))
            else:
                logger.info("No Axis cameras found")
        except Exception as e:
            logger.error(f"Error during camera discovery: {str(e)}")

    def run(self):
        try:
            # Clear all streams from config.json
            clear_streams()

            logger.info("Scanning for cameras")
            self.find_cameras()

            logger.info("Starting MQTT broker")
            self.broker.start()

            logger.info("Connecting MQTT client")
            self.mqtt_client.connect()
            self.mqtt_client.start_background_loop()

            # Initialize the map holder
            map_hol = MapManager(
                "Local House",
                [
                    (59.3250, 18.0700),  # top-left
                    (59.3240, 18.0700),  # bl
                    (59.3250, 18.0710),  # tr
                    (59.3240, 18.0710),
                ],
                "static/floor_plan.jpg",
            )

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
            logger.info("Application shutdown complete")


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
