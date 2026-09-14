"""
Trains a basic RandomForest threat classifier on synthetic data and
saves it to app/services/models/threat_classifier.joblib.

This is intentionally simple, matching the synopsis's scope ("basic
AI-based detection mechanism") — swap in real labeled sensor/audio
data later without changing any API code, since threat_detector.py
just loads whatever .joblib is at that path.

Run once during setup:
    python train_model.py

Features (synthetic, replace with real feature engineering later):
  0: accelerometer jerk magnitude (normalized 0-1)
  1: audio amplitude spike (normalized 0-1)
  2: gyroscope variance (normalized 0-1)
"""

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from pathlib import Path

rng = np.random.default_rng(42)

N = 2000
# Normal situations: low, calm feature values
normal = rng.normal(loc=0.2, scale=0.1, size=(N // 2, 3)).clip(0, 1)
# Panic situations: sharp spikes across all three features
panic = rng.normal(loc=0.8, scale=0.12, size=(N // 2, 3)).clip(0, 1)

X = np.vstack([normal, panic])
y = np.array([0] * (N // 2) + [1] * (N // 2))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print(f"Accuracy:  {accuracy_score(y_test, y_pred):.3f}")
print(f"Precision: {precision_score(y_test, y_pred):.3f}")
print(f"Recall:    {recall_score(y_test, y_pred):.3f}")
print(f"F1-score:  {f1_score(y_test, y_pred):.3f}")

output_dir = Path("app/services/models")
output_dir.mkdir(parents=True, exist_ok=True)
joblib.dump(model, output_dir / "threat_classifier.joblib")
print(f"Saved model to {output_dir / 'threat_classifier.joblib'}")
