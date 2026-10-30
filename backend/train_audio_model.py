
import os
import glob
import joblib
import librosa
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = os.path.join(BASE_DIR, "dataset", "audio")
MODEL_DIR = os.path.join(BASE_DIR, "model")

os.makedirs(MODEL_DIR, exist_ok=True)

SAMPLE_RATE = 16000
DURATION = 5
N_MFCC = 20

AUDIO_EXTENSIONS = ["*.wav", "*.mp3", "*.m4a", "*.ogg"]


def extract_features(file_path):

    audio, sr = librosa.load(
        file_path,
        sr=SAMPLE_RATE,
        mono=True,
        duration=DURATION
    )

    if len(audio) < SAMPLE_RATE:
        raise ValueError("Audio is shorter than one second.")

    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sr,
        n_mfcc=N_MFCC
    )

    return np.concatenate([
        np.mean(mfcc, axis=1),
        np.std(mfcc, axis=1)
    ])


features = []
labels = []

for label in ["real", "fake"]:

    folder = os.path.join(DATASET_DIR, label)

    files = []

    for extension in AUDIO_EXTENSIONS:
        files.extend(glob.glob(os.path.join(folder, extension)))

    print(f"{label.upper()} audio files: {len(files)}")

    for file_path in files:

        try:
            feature = extract_features(file_path)

            features.append(feature)
            labels.append(label)

        except Exception as error:
            print("Skipping:", os.path.basename(file_path), error)


if len(features) == 0:
    raise ValueError("No usable audio files found.")

if len(set(labels)) < 2:
    raise ValueError("You need both real and fake audio recordings.")

if min(labels.count("real"), labels.count("fake")) < 2:
    raise ValueError(
        "You need at least two usable files in each class."
    )


X = np.array(features)
y = np.array(labels)

print("\nDataset shape:", X.shape)
print("Total recordings:", len(y))

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    ))
])

print("\nTraining audio model...")

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nModel Training Completed")
print("Test Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(y_test, predictions))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

model_path = os.path.join(
    MODEL_DIR,
    "audio_deepfake_model.joblib"
)

joblib.dump(model, model_path)

print("\nAudio model saved successfully:")
print(model_path)
