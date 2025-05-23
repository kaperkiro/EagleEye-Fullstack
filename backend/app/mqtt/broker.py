import socket
import subprocess
from app.logger import get_logger
import os

logger = get_logger("MQTT BROKER")


class BrokerManager:
    """Start, stop, and monitor a Mosquitto MQTT broker based on given config."""

    def __init__(
        self,
        host="localhost",
        port=1883,
        config_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "external",
            "mosquitto.conf",
        ),
    ):
        """Initialize BrokerManager with host, port, and config file, then start broker."""
        self.host = host
        self.port = port
        self.config_file = config_file
        self.process = None
        self.start()

    def __del__(self):
        """Ensure broker process is stopped upon object deletion."""
        self.stop()

    def is_running(self) -> bool:
        """Return True if broker is accepting connections on host and port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect((self.host, self.port))
                return True
            except (socket.timeout, ConnectionRefusedError):
                return False

    def stop(self) -> None:
        """Stop the running broker process if it is active."""
        if self.is_running():
            logger.info("Stopping Mosquitto broker...")
            self.process.kill()

    def start(self) -> None:
        """Launch Mosquitto broker with the specified config if not already running."""
        if self.is_running():
            logger.info("Mosquitto broker is already running.")
            return
        else:
            logger.info("Starting Mosquitto broker...")
            self.process = subprocess.Popen(
                f"mosquitto -c {self.config_file}", shell=True
            )
            # add -v flag to enable verbose logging
            # mosquitto -c {self.config.config_file} -v
