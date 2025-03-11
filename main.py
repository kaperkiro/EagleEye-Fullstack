from broker_manager import BrokerManager, BrokerConfig
from database import Database
from mqtt_client import MqttClient
from rtsp_stream import RtspStream
from camera_discovery import CameraDiscovery
from threading import Thread
import time
import logging

logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        self.broker_config = BrokerConfig()
        self.broker = BrokerManager(self.broker_config)
        self.db = Database()
        self.mqtt_client = MqttClient()
        self.streams = {}
        self.discovery = CameraDiscovery()
        self.running = True

    def _start_stream(self, camera_id: int, rtsp_url: str):
        logger.info(f"Starting stream for camera {camera_id} at {rtsp_url}")
        stream = RtspStream(camera_id, rtsp_url, self.mqtt_client, self.db)
        stream.run()

    def _discover_and_add_cameras(self):
        while self.running:
            logger.info("Starting camera discovery")
            detected = self.discovery.discover()
            for ip_suffix, rtsp_url in detected:
                ip = f"192.168.0.{ip_suffix}"
                camera_id = self.db.add_camera(f"Camera_{ip_suffix}", "Auto-detected", 
                                             ip, rtsp_url)
                if camera_id not in self.streams:
                    self._start_stream(camera_id, rtsp_url)
            failed_streams = [(cid, s) for cid, s in self.streams.items() if not s.capture or not s.capture.isOpened()]
            for cam_id, stream in failed_streams:
                logger.info(f"Retrying failed stream for camera {cam_id}")
                stream.release()
                del self.streams[cam_id]
                cameras = self.db.get_cameras()
                for cid, _, _, _, url in cameras:
                    if cid == cam_id:
                        self._start_stream(cid, url)
                        break
            time.sleep(60)

    def run(self):
        try:
            logger.info("Starting MQTT broker")
            self.broker.start()

            logger.info("Connecting MQTT client")
            self.mqtt_client.connect()
            self.mqtt_client.start_background_loop()

            logger.info("Starting discovery thread")
            discovery_thread = Thread(target=self._discover_and_add_cameras, daemon=True)
            discovery_thread.start()

            logger.info("Loading existing cameras from database")
            cameras = self.db.get_cameras()
            
            for cam_id, name, location, ip, rtsp_url in cameras:
                if cam_id not in self.streams:  # Only start known working camera
                    self._start_stream(cam_id, rtsp_url)


            while self.running:
                time.sleep(1)

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
        finally:
            self.running = False
            for stream in self.streams.values():
                stream.release()
            self.mqtt_client.stop()
            logger.info("Application shutdown complete")

def main():
    app = Application()
    app.run()

if __name__ == "__main__":
    main()