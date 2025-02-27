import cv2
import os
import numpy as np
import logging
from typing import Optional
from database import Database
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
TIME_TO_UPDATE_THUMBNAIL = 30  # seconds

class RtspStream:
    def __init__(self, camera_id: int, rtsp_url: str, mqtt_client, db: Database):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.mqtt_client = mqtt_client
        self.db = db
        self.capture: Optional[cv2.VideoCapture] = None
        self.window_name = f"Camera {camera_id}"
        self._setup_environment()
        
    def _setup_environment(self) -> None:
        # Adjusted for stability: larger buffer, more analysis time
        # os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout=5000|fflags=nobuffer|probesize=2000000|analyzeduration=5000000|buffer_size=1024000"
        
        # Force OpenCV to use TCP for RTSP (improves stability)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        
        logger.info(f"Setting up RTSP environment for {self.rtsp_url}")
    
    def connect(self, retries: int = 3, delay: int = 2) -> bool:
        attempt = 0
        while attempt < retries:
            try:
                logger.info(f"Attempt {attempt + 1}/{retries} to connect to RTSP stream: {self.rtsp_url}")
                self.capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                if not self.capture.isOpened():
                    logger.error(f"Failed to open RTSP stream for camera {self.camera_id}")
                    raise Exception("Stream not opened")
                
                self.capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                self.capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 10)  # Larger buffer for stability
                
                # Wait for stream to stabilize
                # time.sleep(1)  # Give stream 1s to start
                ret, frame = None, None
                for i in range(30):  # Try up to 30 frames
                    ret, frame = self.capture.read()
                    logger.debug(f"Frame read attempt {i+1}: ret={ret}, frame={frame is not None}")
                    if ret and frame is not None and frame.size > 0:
                        break
                    time.sleep(0.1)
                if not ret or frame is None or frame.size == 0:
                    logger.error(f"Cannot read valid frame from RTSP stream: {self.rtsp_url}")
                    raise Exception("No valid frames read after 30 attempts")
                
                logger.info(f"Successfully connected to RTSP stream for camera {self.camera_id}")
                return True
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                self._force_release()
                attempt += 1
                if attempt < retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        logger.error(f"All {retries} attempts to connect to {self.rtsp_url} failed")
        return False
    
    def _force_release(self) -> None:
        try:
            if self.capture is not None:
                self.capture.release()
                logger.debug(f"Released capture for {self.rtsp_url}")
            self.capture = None
        except Exception as e:
            logger.error(f"Error forcing release for {self.rtsp_url}: {str(e)}")
    
    def _draw_detections(self, frame: np.ndarray) -> np.ndarray:
        # print("Getting detections for camera", self.camera_id)
        detections = self.mqtt_client.get_detections(self.camera_id)
        if not detections:
            # print("No detections")
            return frame
            
        frame_height, frame_width = frame.shape[:2]
        for detection in detections:
            bbox = detection.get("bounding_box", {})
            class_info = detection.get("class", {})
            
            left = int(bbox.get("left", 0) * frame_width)
            top = int(bbox.get("top", 0) * frame_height)
            right = int(bbox.get("right", 0) * frame_width)
            bottom = int(bbox.get("bottom", 0) * frame_height)
            
            color = (0, 255, 0)
            thickness = 2
            cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)
            
            if class_info:
                label = class_info.get("type", "Unknown")
                cv2.putText(frame, label, (left, top-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame
    
    def _frame_to_bytes(self, frame: np.ndarray) -> bytes:
        """Convert a frame to JPEG bytes."""
        try:
            # Resize frame to a smaller thumbnail size (e.g., 320x240)
            thumbnail = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_AREA)
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', thumbnail)
            if not ret:
                raise Exception("Failed to encode frame to JPEG")
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"Error converting frame to bytes for camera {self.camera_id}: {str(e)}")
            return b''
    
    def run(self) -> None:
        frame_count = 0
        while True:
            try:
                if not self.capture or not self.capture.isOpened():
                    logger.warning(f"Capture not open for camera {self.camera_id}, attempting reconnect")
                    if not self.connect():
                        break
                    continue
                
                ret, frame = self.capture.read()
                if not ret or frame is None or frame.size == 0:
                    logger.warning(f"Failed to grab frame for camera {self.camera_id}, skipping frame")
                    time.sleep(0.1)  # Brief pause before retry
                    continue
                
                logger.debug(f"Frame {frame_count} read successfully for camera {self.camera_id}")
                frame_with_detections = self._draw_detections(frame)
                cv2.imshow(self.window_name, frame_with_detections)
                logger.debug(f"Displayed frame {frame_count} for camera {self.camera_id}")
                
                # Save thumbnail every 30 sec (900 frames at 30 fps)
                if frame_count % 900 == 0:
                    thumbnail_bytes = self._frame_to_bytes(frame_with_detections)
                    if thumbnail_bytes:
                        self.db.update_camera_thumbnail(self.camera_id, thumbnail_bytes)
                        logger.info(f"Saved thumbnail as bytes for camera {self.camera_id}")
                
                frame_count += 1
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
            except Exception as e:
                logger.error(f"Error in stream loop for camera {self.camera_id}: {str(e)}")
                time.sleep(1)
                self._force_release()
                if not self.connect():
                    break
    
    def release(self) -> None:
        self._force_release()
        try:
            cv2.destroyWindow(self.window_name)
            logger.info(f"Released RTSP stream for camera {self.camera_id}")
        except Exception as e:
            logger.error(f"Error releasing window for camera {self.camera_id}: {str(e)}")