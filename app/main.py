import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mqtt.broker import BrokerManager
from app.mqtt.client import MqttClient
from app.camera.webrtc import start_rtsp_to_webrtc, clear_streams
from app.server import Server
from app.map.manager import MapManager
from app.camera.arp_scan import find_cameras, add_cameras
from app.alarms.alarm import AlarmManager
from app.objects.manager import ObjectManager
from app.logger import get_logger

logger = get_logger("MAIN")

import threading


class Application:
    def __init__(self):
        self.running = True

        logger.info("Initializing application")
        clear_streams()

        self.cameras = add_cameras()
        self.map_manager = MapManager(self.cameras)
        self.alarm_manager = AlarmManager()
        self.object_manager = ObjectManager(self.map_manager, self.alarm_manager)
        self.broker = BrokerManager()
        self.mqtt_client = MqttClient(self.object_manager)

        self.webrtc_thread = threading.Thread(target=start_rtsp_to_webrtc, daemon=True)
        self.webrtc_thread.start()

        self.server_thread = threading.Thread(
            target=Server,
            args=(self.mqtt_client, self.map_manager, self.alarm_manager),
            daemon=True,
        )
        self.server_thread.start()

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
            logger.info(
                "Keyboard interrupt received, stopping application, please wait..."
            )
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
