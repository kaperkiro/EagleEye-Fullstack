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


# @app.route("/api/login", methods=["POST"])
# def login():
#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")
#     if not username or not password:
#         return jsonify({"message": "Username and password are required"}), 400
#     if db.verify_user(username, password):
#         return jsonify({"message": "Login successful"}), 200
#     return jsonify({"message": "Invalid username or password"}), 401


if __name__ == "__main__":
    app.run(debug=True, port=5000)
