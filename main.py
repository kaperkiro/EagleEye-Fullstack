from broker_manager import BrokerManager
from database import Database
from mqtt_client import MqttClient
from webrtc_server import start_rtsp_to_webrtc
from server import run_flask_server
import threading
import time
import logging
from camera import Camera, clear_streams
from calibration import Calibration
from map_manager import MapManager

logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.broker = BrokerManager()
        self.db = Database()
        self.mqtt_client = MqttClient()
        self.running = True
        self.cameras = []

    def run(self):
        try:
            logger.info("Starting MQTT broker")
            self.broker.start()

            logger.info("Connecting MQTT client")
            self.mqtt_client.connect()
            self.mqtt_client.start_background_loop()
            # Clear all streams from config.json
            clear_streams()
            # Add cameras to config.json
            test_cam = Camera()

            # Initialize the map holder
            map_hol = MapManager(
                "Local House",
                [
                    (59.3250, 18.0700),  # top-left
                    (59.3240, 18.0700),  # bl
                    (59.3250, 18.0710),  # tr
                    (59.3240, 18.0710),
                ],
                "assets/floor_plan.jpg",
            )
            logger.info("Starting RTSP to WebRTC server")
            threading.Thread(target=start_rtsp_to_webrtc, daemon=True).start()

            logger.info("Starting Flask server")
            threading.Thread(
                target=run_flask_server, args=(self.mqtt_client, map_hol), daemon=True
            ).start()

            logger.info("Starting camera configuration")
            # Calibration(test_cam, self.mqtt_client)

            self.cameras.append(test_cam)

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
