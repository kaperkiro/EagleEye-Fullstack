from broker_manager import BrokerManager
from database import Database
from mqtt_client import MqttClient
from webrtc_server import start_rtsp_to_webrtc
import time
import logging

logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        self.broker = BrokerManager()
        self.db = Database()
        self.mqtt_client = MqttClient()
        self.running = True

    def run(self):
        try:
            logger.info("Starting MQTT broker")
            self.broker.start()

            logger.info("Connecting MQTT client")
            self.mqtt_client.connect()
            self.mqtt_client.start_background_loop()

            logger.info("Starting RTSP to WebRTC server")
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