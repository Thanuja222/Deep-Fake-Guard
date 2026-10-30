
import os
import uuid
import joblib
import librosa
import numpy as np

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename


audio_bp = Blueprint("audio_detection", __name__)

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR, "model", "audio_deepfake_model.joblib"
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR, "backend", "uploads", "audio"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "ogg"}

SAMPLE_RATE = 16000
DURATION = 5
N_MFCC = 20


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_audio_features(file_path):

    audio, sr = librosa.load(
        file_path,
        sr=SAMPLE_RATE,
        mono=True,
        duration=DURATION
    )

    if len(audio) < SAMPLE_RATE:
        raise ValueError("Audio must contain at least one second.")

    # MFCC feature extraction
    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sr,
        n_mfcc=N_MFCC
    )

    # Mean and standard deviation of each MFCC
    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    features = np.concatenate([mfcc_mean, mfcc_std])

    return features.reshape(1, -1)


@audio_bp.route("/api/analyze/audio", methods=["POST"])
def analyze_audio():

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No audio file uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "Please select an audio file."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Only WAV, MP3, M4A and OGG files are supported."
        }), 400

    if not os.path.exists(MODEL_PATH):
        return jsonify({
            "success": False,
            "error": "Audio model not found. Train the audio model first."
        }), 503

    filename = secure_filename(file.filename)

    # Unique filename prevents overwriting another upload
    filename = str(uuid.uuid4()) + "_" + filename

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        file.save(file_path)

        features = extract_audio_features(file_path)

        model = joblib.load(MODEL_PATH)

        prediction = model.predict(features)[0]

        probabilities = model.predict_proba(features)[0]

        confidence = float(np.max(probabilities)) * 100

        return jsonify({
            "success": True,
            "filename": file.filename,
            "prediction": str(prediction).upper(),
            "confidence": round(confidence, 2),
            "message": (
                "Likely AI-generated audio"
                if str(prediction).lower() == "fake"
                else "Likely genuine audio"
            )
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:

        if os.path.exists(file_path):
            os.remove(file_path)
