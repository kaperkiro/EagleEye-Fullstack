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

            logger.info("Starting Flask server")

            #Clear all streams from config.json and add cameras
            clear_streams()
            # Add cameras to config.json
            test_cam = Camera("camera1")
            # test_cam.configure_camera(15.00001, 16.00002, 100, 61)
            test_cam.save_snapshot()

            Calibration(test_cam.id)
            
            self.cameras.append(test_cam)
            
            # Start the Flask server in a separate thread
            threading.Thread(target=run_flask_server, args=(self.mqtt_client,)).start()
            logger.info("Starting Flask server")
            logger.info("Starting RTSP to WebRTC server")
            # Create camera objects add them to config 
            start_rtsp_to_webrtc()

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
