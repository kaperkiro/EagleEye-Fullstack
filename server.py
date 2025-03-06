# backend/server.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from database import Database
import base64
import os
import sqlite3

app = Flask(__name__)
CORS(app)
db = Database()
MAP_PATH = "map.jpg"  # Store the map locally for simplicity


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    if db.verify_user(username, password):
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"message": "Invalid username or password"}), 401


@app.route("/api/cameras", methods=["GET"])
def get_cameras():
    cameras = db.get_cameras()
    camera_list = []
    for camera in cameras:
        camera_id, name, location, ip, rtsp_url = camera
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT THUMBNAIL FROM Camera WHERE ID = ?", (camera_id,))
            thumbnail = cursor.fetchone()
            thumbnail_data = (
                base64.b64encode(thumbnail[0]).decode("utf-8")
                if thumbnail and thumbnail[0]
                else None
            )
        camera_list.append(
            {
                "id": camera_id,
                "name": name,
                "location": location,
                "ip": ip,
                "rtspUrl": rtsp_url,
                "thumbnail": thumbnail_data,
            }
        )
    return jsonify(camera_list), 200


@app.route("/api/upload_map", methods=["POST"])
def upload_map():
    if "map" not in request.files:
        return jsonify({"message": "No map file provided"}), 400
    file = request.files["map"]
    if file and file.filename.endswith((".jpg", ".jpeg", ".png")):
        file.save(MAP_PATH)
        return jsonify({"message": "Map uploaded successfully"}), 200
    return jsonify({"message": "Invalid file type"}), 400


@app.route("/api/get_map", methods=["GET"])
def get_map():
    if os.path.exists(MAP_PATH):
        return send_file(MAP_PATH, mimetype="image/jpeg")
    return jsonify({"message": "No map uploaded yet"}), 404


@app.route("/api/delete_map", methods=["DELETE"])
def delete_map():
    try:
        os.remove(MAP_PATH)
        return jsonify({"message": "Map deleted successfully"}), 200
    except FileNotFoundError:
        return jsonify({"message": "No map to delete"}), 404


@app.route("/api/camera_position", methods=["POST"])
def save_camera_position():
    data = request.get_json()
    camera_id = data.get("camera_id")
    x = data.get("x")
    y = data.get("y")
    if not all([camera_id, x, y]):
        return jsonify({"message": "Missing camera_id, x, or y"}), 400
    db.save_camera_position(camera_id, x, y)
    return jsonify({"message": "Camera position saved"}), 200


@app.route("/api/camera_position/<int:camera_id>", methods=["DELETE"])
def delete_camera_position(camera_id):
    db.delete_camera_position(camera_id)
    return jsonify({"message": "Camera position deleted"}), 200


@app.route("/api/camera_positions", methods=["GET"])
def get_camera_positions():
    positions = db.get_camera_positions()
    return jsonify(positions), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
