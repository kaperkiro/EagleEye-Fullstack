import cv2
import os
import subprocess
from threading import Thread
from queue import Queue
from typing import List, Tuple
from config import RtspConfig
import logging
import platform

logger = logging.getLogger(__name__)


class CameraDiscovery:
    def __init__(
        self,
        base_ip: str = "192.168.0.",
        start_range: int = 90,
        end_range: int = 100,
        username: str = "student",
        password: str = "student_pass",
    ):
        self.base_ip = base_ip
        self.start_range = start_range
        self.end_range = end_range
        self.username = username
        self.password = password
        self.detected_cameras: List[Tuple[int, str]] = []
        self.queue = Queue()

    def _ping(self, ip: str) -> bool:
        """Ping the IP to check if a device is present."""
        # Adjust ping command based on OS
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "4", ip]  # 4 pings
        try:
            # Run ping silently and check if it succeeds
            output = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
            )
            return output.returncode == 0  # 0 means success
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            logger.debug(f"Ping failed for {ip}: {str(e)}")
            return False

    def _test_rtsp(self, ip: str) -> bool:
        """Test RTSP stream availability at the given IP."""
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            "rtsp_transport;tcp|timeout=3000|fflags=nobuffer|probesize=1000000|analyzeduration=2000000"
        )
        config = RtspConfig(username=self.username, password=self.password, ip=ip)
        logger.info(f"Testing RTSP at {ip}")
        cap = cv2.VideoCapture(config.url, cv2.CAP_FFMPEG)
        try:
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
                ret, _ = cap.read()
                if ret:
                    logger.info(f"RTSP stream found at {ip}")
                    return True
                else:
                    logger.debug(f"RTSP opened but no frames at {ip}")
            else:
                logger.debug(f"No RTSP stream at {ip}")
        finally:
            cap.release()
        return False

    def _scan_ip(self, ip_suffix: int):
        ip = f"{self.base_ip}{ip_suffix}"
        if self._ping(ip):
            logger.debug(f"Ping succeeded for {ip}, checking RTSP")
            if self._test_rtsp(ip):
                config = RtspConfig(
                    username=self.username, password=self.password, ip=ip
                )
                self.queue.put((ip_suffix, config.url))
        else:
            logger.debug(f"No device responding at {ip}, skipping RTSP test")

    def discover(self) -> List[Tuple[int, str]]:
        self.detected_cameras.clear()
        threads = []
        logger.info(
            f"Scanning IP range {self.base_ip}{self.start_range}-{self.end_range}"
        )
        for i in range(self.start_range, self.end_range + 1):
            t = Thread(target=self._scan_ip, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        while not self.queue.empty():
            self.detected_cameras.append(self.queue.get())

        if not self.detected_cameras:
            logger.warning("No cameras detected in the specified range")
        return self.detected_cameras
