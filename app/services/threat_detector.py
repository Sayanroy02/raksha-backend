"""
M5 — AI Threat Detector.

Loads a trained scikit-learn classifier if one exists at MODEL_PATH.
If no model has been trained yet, falls back to a simple threshold
heuristic so the endpoint still works during early development —
replace this once train_model.py has produced a real .joblib file.

Model artifacts are git-ignored (see .gitignore) since they're
regenerable and can be large — train them locally / on first deploy.
"""

from pathlib import Path

import joblib
import numpy as np

MODEL_PATH = Path(__file__).parent / "models" / "threat_classifier.joblib"
CONFIDENCE_THRESHOLD = 0.75

_model = None
_model_loaded_from_disk = False

if MODEL_PATH.exists():
    _model = joblib.load(MODEL_PATH)
    _model_loaded_from_disk = True


def predict_threat(features: list[float]) -> tuple[float, bool, str]:
    """
    Returns (confidence, auto_triggered, model_used).
    features: engineered feature vector, e.g.
      [accel_jerk_magnitude, audio_amplitude_spike, gyro_variance, ...]
    """
    x = np.array(features).reshape(1, -1)

    if _model_loaded_from_disk:
        confidence = float(_model.predict_proba(x)[0][1])
        model_used = "sklearn_random_forest_v1"
    else:
        # Fallback heuristic: normalized mean of features as a stand-in
        # score until a real model is trained. Never returns auto-trigger
        # above the threshold unless features are genuinely extreme.
        confidence = float(min(max(np.mean(x), 0.0), 1.0))
        model_used = "heuristic_fallback"

    auto_triggered = confidence >= CONFIDENCE_THRESHOLD
    return confidence, auto_triggered, model_used
