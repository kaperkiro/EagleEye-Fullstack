import socket
import subprocess
from app.logger import get_logger

logger = get_logger("MQTT BROKER")

class BrokerManager:
    def __init__(
        self, host="localhost", port=1883, config_file="external/mosquitto.conf"
    ):
        self.host = host
        self.port = port
        self.config_file = config_file
        self.process = None
        self.start()

    def __del__(self):
        self.stop()

    def is_running(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect((self.host, self.port))
                return True
            except (socket.timeout, ConnectionRefusedError):
                return False
            
    def stop(self) -> None:
        if self.is_running():
            logger.info("Stopping Mosquitto broker...")
            self.process.kill()

    def start(self) -> None:
        if self.is_running():
            logger.info("Mosquitto broker is already running.")
            return
        else:
            logger.info("Starting Mosquitto broker...")
            self.process = subprocess.Popen(f"mosquitto -c {self.config_file}", shell=True)  
            # add -v flag to enable verbose logging
            # mosquitto -c {self.config.config_file} -v
