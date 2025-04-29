import sqlite3
from datetime import datetime, timedelta
import os
import cv2
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Existing tables
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS Camera (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME TEXT NOT NULL,
                LOCATION TEXT NOT NULL,
                IP TEXT NOT NULL,
                RTSPURL TEXT NOT NULL,
                THUMBNAIL BLOB)"""
            )

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS Videoframe (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                TIMESTAMP TEXT NOT NULL,
                TIMETOLIVE TEXT NOT NULL,
                FILEPATH TEXT NOT NULL,
                CAMERAID INTEGER NOT NULL,
                FOREIGN KEY (CAMERAID) REFERENCES Camera(ID))"""
            )

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS DetectedObject (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                GEOPOSITION TEXT NOT NULL,
                IMAGEVELOCITY REAL NOT NULL,
                TOPLEFTBOXX INTEGER NOT NULL,
                TOPLEFTBOXY INTEGER NOT NULL,
                BOTTOMRIGHTBOXX INTEGER NOT NULL,
                BOTTOMRIGHTBOXY INTEGER NOT NULL,
                VIDEODFRAMEID INTEGER NOT NULL,
                FOREIGN KEY (VIDEODFRAMEID) REFERENCES Videoframe(ID))"""
            )

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS Human (
                ID INTEGER PRIMARY KEY,
                SCORE REAL NOT NULL,
                UPPERCOLOR TEXT NOT NULL,
                LOWERCOLOR TEXT NOT NULL,
                FOREIGN KEY (ID) REFERENCES DetectedObject(ID))"""
            )

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS Vehicle (
                ID INTEGER PRIMARY KEY,
                SCORE REAL NOT NULL,
                VEHICLETYPE TEXT NOT NULL,
                COLOR TEXT NOT NULL,
                FOREIGN KEY (ID) REFERENCES DetectedObject(ID))"""
            )

            # cursor.execute('''CREATE TABLE IF NOT EXISTS Users (          # Ska vi ta bort users helt och hållet?
            #     ID INTEGER PRIMARY KEY AUTOINCREMENT,
            #     USERNAME TEXT UNIQUE NOT NULL,
            #     PASSWORD TEXT NOT NULL)''')

            conn.commit()

    # Existing methods (unchanged)
    def update_camera_thumbnail(self, camera_id: int, thumbnail_bytes: bytes) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE Camera SET THUMBNAIL = ? WHERE ID = ?",
                    (thumbnail_bytes, camera_id),
                )
                conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(
                        f"No camera found with ID {camera_id} to update thumbnail"
                    )
        except Exception as e:
            logger.error(f"Error updating thumbnail for camera {camera_id}: {str(e)}")

    def add_camera(self, name: str, location: str, ip: str, rtsp_url: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ID FROM Camera WHERE IP = ?", (ip,))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            cursor.execute(
                "INSERT INTO Camera (NAME, LOCATION, IP, RTSPURL) VALUES (?, ?, ?, ?)",
                (name, location, ip, rtsp_url),
            )
            conn.commit()
            return cursor.lastrowid

    def get_cameras(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ID, NAME, LOCATION, IP, RTSPURL FROM Camera")
            return cursor.fetchall()

    def save_frame(self, camera_id, frame, detections):
        timestamp = datetime.now()
        ttl = timestamp + timedelta(minutes=30)
        filepath = f"frames/frame_{timestamp.strftime('%Y%m%d_%H%M%S')}_{camera_id}.jpg"
        os.makedirs("frames", exist_ok=True)
        cv2.imwrite(filepath, frame)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Videoframe (TIMESTAMP, TIMETOLIVE, FILEPATH, CAMERAID) VALUES (?, ?, ?, ?)",
                (timestamp.isoformat(), ttl.isoformat(), filepath, camera_id),
            )
            frame_id = cursor.lastrowid

            for det in detections:
                bbox = det.get("bounding_box", {})
                class_info = det.get("class", {})
                obj_id = self._save_detected_object(cursor, frame_id, bbox)

                if class_info.get("type") == "Human":
                    self._save_human(cursor, obj_id, class_info)
                elif class_info.get("type") == "Car":
                    self._save_vehicle(cursor, obj_id, class_info)
            conn.commit()

    def _save_detected_object(self, cursor, frame_id, bbox):
        cursor.execute(
            "INSERT INTO DetectedObject (GEOPOSITION, IMAGEVELOCITY, TOPLEFTBOXX, TOPLEFTBOXY, BOTTOMRIGHTBOXX, BOTTOMRIGHTBOXY, VIDEODFRAMEID) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "Unknown",
                0.0,
                int(bbox.get("left", 0) * 1000),
                int(bbox.get("top", 0) * 1000),
                int(bbox.get("right", 0) * 1000),
                int(bbox.get("bottom", 0) * 1000),
                frame_id,
            ),
        )
        return cursor.lastrowid

    def _save_human(self, cursor, obj_id, class_info):
        upper = class_info.get("upper_clothing_colors", [{}])[0].get("name", "Unknown")
        lower = class_info.get("lower_clothing_colors", [{}])[0].get("name", "Unknown")
        score = class_info.get("score", 0.0)
        cursor.execute(
            "INSERT INTO Human (ID, SCORE, UPPERCOLOR, LOWERCOLOR) VALUES (?, ?, ?, ?)",
            (obj_id, score, upper, lower),
        )

    def _save_vehicle(self, cursor, obj_id, class_info):
        color = class_info.get("colors", [{}])[0].get("name", "Unknown")
        score = class_info.get("score", 0.0)
        cursor.execute(
            "INSERT INTO Vehicle (ID, SCORE, VEHICLETYPE, COLOR) VALUES (?, ?, ?, ?)",
            (obj_id, score, "Car", color),
        )

    # def verify_user(self, username: str, password: str) -> bool:                                  # Ta bort users?
    #     """Verify if the username and password match a record in the Users table."""
    #     with sqlite3.connect(self.db_path) as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT * FROM Users WHERE USERNAME = ? AND PASSWORD = ?",
    #                       (username, password))
    #         user = cursor.fetchone()
    #         return user is not None


if __name__ == "__main__":
    # Test the database initialization
    db = Database()
    print("Database initialized. Test user: 'testuser', 'testpass'")
