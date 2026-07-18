"""
Trains a Random Forest classifier for crop recommendation.
Uses synthetic data based on known agronomic ranges for 23 crops.

Run from backend/ folder with venv active:
    python scripts/train_crop_model.py
"""

import os
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder


os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_PATH = "api/ml/crop_model.pkl"


# Crop parameter ranges
# Each crop:
# [N_min, N_max, P_min, P_max, K_min, K_max,
#  temp_min, temp_max, humidity_min, humidity_max,
#  ph_min, ph_max, rainfall_min, rainfall_max]

CROP_RANGES = {
    "rice":        [60,140, 35,75,  35,75,  20,28, 70,90, 5.5,7.0, 150,300],
    "wheat":       [60,120, 40,80,  40,80,  10,25, 50,70, 6.0,7.5, 50,150],
    "maize":       [60,120, 35,75,  35,75,  18,28, 55,75, 5.8,7.5, 60,120],
    "chickpea":    [20,50,  60,100, 60,100, 15,25, 40,60, 6.0,8.0, 40,100],
    "kidneybeans": [15,35,  50,90,  50,90,  15,25, 55,75, 5.5,7.0, 80,150],
    "pigeonpeas":  [15,35,  50,90,  50,90,  22,32, 55,75, 5.5,7.0, 60,120],
    "mothbeans":   [15,35,  45,85,  45,85,  22,32, 40,60, 6.0,7.5, 30,80],
    "mungbean":    [15,35,  45,85,  45,85,  22,32, 60,80, 6.0,7.5, 60,120],
    "blackgram":   [20,45,  50,90,  50,90,  22,32, 60,80, 5.5,7.0, 60,130],
    "lentil":      [15,35,  55,95,  55,95,  15,25, 50,70, 6.0,8.0, 35,85],
    "pomegranate": [15,35,  40,80,  40,80,  18,32, 55,75, 5.5,7.5, 60,120],
    "banana":      [80,150, 55,95,  55,95,  22,32, 70,90, 5.5,7.0, 100,200],
    "mango":       [15,35,  25,65,  25,65,  22,32, 45,65, 5.5,7.5, 60,120],
    "grapes":      [15,35,  25,65,  25,65,  15,28, 55,75, 5.5,7.5, 65,130],
    "watermelon":  [80,140, 40,80,  40,80,  22,32, 70,90, 6.0,7.5, 40,100],
    "muskmelon":   [80,140, 40,80,  40,80,  22,32, 80,100,6.0,7.5, 20,80],
    "apple":       [15,35,  20,60,  20,60,  15,25, 80,100,5.5,6.5, 100,200],
    "orange":      [15,35,  15,55,  15,55,  15,30, 60,80, 6.0,7.5, 80,160],
    "papaya":      [40,80,  35,75,  35,75,  25,35, 70,90, 6.0,7.5, 100,200],
    "coconut":     [15,35,  15,55,  15,55,  25,35, 70,90, 5.5,7.5, 100,220],
    "cotton":      [100,160,35,75,  35,75,  22,32, 55,75, 6.0,8.0, 60,120],
    "jute":        [60,120, 35,75,  35,75,  22,32, 65,85, 6.0,7.5, 150,250],
    "coffee":      [90,150, 35,75,  35,75,  18,28, 75,95, 5.5,6.5, 150,300],
}


SAMPLES_PER_CROP = 200
np.random.seed(42)

rows = []

for crop, r in CROP_RANGES.items():
    for _ in range(SAMPLES_PER_CROP):
        rows.append({
            "N": np.random.uniform(r[0], r[1]),
            "P": np.random.uniform(r[2], r[3]),
            "K": np.random.uniform(r[4], r[5]),
            "temperature": np.random.uniform(r[6], r[7]),
            "humidity": np.random.uniform(r[8], r[9]),
            "ph": np.random.uniform(r[10], r[11]),
            "rainfall": np.random.uniform(r[12], r[13]),
            "label": crop,
        })


df = pd.DataFrame(rows)

print(
    f"Dataset: {len(df)} samples across "
    f"{df['label'].nunique()} crops"
)


X = df[
    [
        "N",
        "P",
        "K",
        "temperature",
        "humidity",
        "ph",
        "rainfall",
    ]
]

y = df["label"]


le = LabelEncoder()
y_encoded = le.fit_transform(y)


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded,
)


print("Training Random Forest...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=4,
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)


y_pred = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    y_pred,
)

print(f"Accuracy: {accuracy * 100:.1f}%")


os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True,
)

joblib.dump(
    {
        "model": model,
        "label_encoder": le,
    },
    OUTPUT_PATH,
)


print(f"Model saved to {OUTPUT_PATH}")

print(
    f"File size: "
    f"{os.path.getsize(OUTPUT_PATH) / 1024:.0f} KB"
)