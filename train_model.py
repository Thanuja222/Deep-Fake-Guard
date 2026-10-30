import os
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import classification_report, roc_auc_score
import numpy as np

# Configurations
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 5
DATASET_DIR = "dataset"
MODEL_SAVE_PATH = "model/deepfake_model.keras"

def train_deepfake_detector():
    if not os.path.exists(os.path.join(DATASET_DIR, "real")) or not os.path.exists(os.path.join(DATASET_DIR, "fake")):
        print("Error: 'dataset/real' or 'dataset/fake' directories are missing!")
        return

    print("[INFO] Loading training and validation datasets...")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary"
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary"
    )

    class_names = train_ds.class_names
    print(f"[INFO] Class Labels found: {class_names}")

    # Prefetching for performance optimization
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

    print("[INFO] Building MobileNetV2 transfer learning architecture...")
    base_model = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base_model.trainable = False  # Freeze backbone

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.3)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    predictions = Dense(1, activation='sigmoid')(x)

    model = Model(inputs=base_model.input, outputs=predictions)

    model.compile(optimizer=Adam(learning_rate=0.0001),
                  loss='binary_crossentropy',
                  metrics=['accuracy', tf.keras.metrics.Precision(name='precision'), tf.keras.metrics.Recall(name='recall')])

    print("[INFO] Training classification head...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )

    print("[INFO] Evaluating performance on validation set...")
    val_steps = tf.data.experimental.cardinality(val_ds).numpy()
    y_true = np.concatenate([y for x, y in val_ds], axis=0)
    y_pred_probs = model.predict(val_ds, steps=val_steps)
    y_pred = (y_pred_probs >= 0.5).astype(int)

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=class_names))
    
    try:
        roc_auc = roc_auc_score(y_true, y_pred_probs)
        print(f"Validation ROC-AUC: {roc_auc:.4f}")
    except Exception as e:
        print(f"Could not compute ROC-AUC: {e}")

    os.makedirs("model", exist_ok=True)
    model.save(MODEL_SAVE_PATH)
    print(f"[SUCCESS] Model successfully saved to {MODEL_SAVE_PATH}")

if __name__ == '__main__':
    train_deepfake_detector()