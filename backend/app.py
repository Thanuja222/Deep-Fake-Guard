
import os
import sqlite3
import time

from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Existing image and video detection functions
from model import analyze_media, analyze_video, calculate_sha256

# Email fraud detection
from email_detection import email_bp

# Audio deepfake detection
from audio_detection import audio_bp


# ==========================================
# FLASK APPLICATION SETUP
# ==========================================

app = Flask(__name__)
CORS(app)

# Register detection modules
app.register_blueprint(email_bp)
app.register_blueprint(audio_bp)


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "database.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_db():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Analysis history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            prediction TEXT,
            confidence REAL,
            sha256 TEXT,
            latency REAL,
            timestamp TEXT
        )
    """)

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==========================================
# HOME ROUTE
# ==========================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "Deep-Fake Guard API is running",
        "modules": [
            "Image Detection",
            "Video Detection",
            "Audio Deepfake Detection",
            "Email Fraud Detection"
        ]
    })


# ==========================================
# USER SIGNUP
# ==========================================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:

        return jsonify({
            "success": False,
            "error": "Username and password are required."
        }), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )

    existing_user = cursor.fetchone()

    if existing_user:

        conn.close()

        return jsonify({
            "success": False,
            "error": "Username already exists."
        }), 409

    hashed_password = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hashed_password)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Registration successful."
    })


# ==========================================
# USER LOGIN
# ==========================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:

        return jsonify({
            "success": False,
            "error": "Username and password are required."
        }), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[0], password):

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "username": username
        })

    return jsonify({
        "success": False,
        "error": "Invalid username or password."
    }), 401


# ==========================================
# IMAGE AND VIDEO DEEPFAKE DETECTION
# ==========================================

@app.route("/api/analyze", methods=["POST"])
def analyze():

    if "file" not in request.files:

        return jsonify({
            "success": False,
            "error": "No file uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "success": False,
            "error": "Please select a file."
        }), 400

    filename = secure_filename(file.filename)

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    start_time = time.time()

    try:

        file.save(file_path)

        # Calculate SHA256 hash
        sha256 = calculate_sha256(file_path)

        extension = filename.rsplit(".", 1)[-1].lower()

        video_extensions = ["mp4", "avi", "mov", "mkv", "webm"]

        # Image detection
        if extension in ["jpg", "jpeg", "png", "bmp", "webp"]:

            prediction, confidence = analyze_media(file_path)

        # Video detection
        elif extension in video_extensions:

            prediction, confidence = analyze_video(file_path)

        else:

            return jsonify({
                "success": False,
                "error": "Unsupported image or video format."
            }), 400

        latency = round(time.time() - start_time, 2)

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Save analysis history
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO history
            (filename, prediction, confidence, sha256, latency, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            filename,
            str(prediction),
            float(confidence),
            sha256,
            latency,
            timestamp
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "filename": filename,
            "prediction": str(prediction),
            "confidence": round(float(confidence), 2),
            "sha256": sha256,
            "hash": sha256,
            "latency": latency,
            "processing_time": latency,
            "timestamp": timestamp
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:

        if os.path.exists(file_path):
            os.remove(file_path)


# ==========================================
# ANALYSIS HISTORY
# ==========================================

@app.route("/api/history", methods=["GET"])
def history():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            filename,
            prediction,
            confidence,
            sha256,
            latency,
            timestamp
        FROM history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    records = []

    for row in rows:

        records.append({
            "id": row[0],
            "filename": row[1],
            "prediction": row[2],
            "confidence": row[3],
            "sha256": row[4],
            "hash": row[4],
            "file_hash": row[4],
            "latency": row[5],
            "processing_time": row[5],
            "timestamp": row[6]
        })

    return jsonify(records)


# ==========================================
# START FLASK SERVER
# ==========================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
