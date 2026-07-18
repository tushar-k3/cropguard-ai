"""
Trains a Random Forest classifier for fertilizer recommendation.
Run from backend/ folder with venv active:
    python scripts/train_fertilizer_model.py
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
OUTPUT_PATH = "api/ml/fertilizer_model.pkl"

# Fertilizer suitability ranges per crop
# [N_min, N_max, P_min, P_max, K_min, K_max, label]
FERTILIZER_DATA = {
    "Urea": [
        ("rice",       [60,140, 20,50,  20,50]),
        ("wheat",      [60,120, 25,55,  25,55]),
        ("maize",      [80,150, 30,60,  30,60]),
        ("sugarcane",  [100,180,30,60,  30,60]),
        ("cotton",     [80,150, 25,55,  25,55]),
        ("jute",       [60,120, 20,50,  20,50]),
    ],
    "DAP": [
        ("rice",       [30,80,  50,100, 30,70]),
        ("wheat",      [30,70,  50,100, 30,70]),
        ("maize",      [40,90,  50,100, 35,75]),
        ("soybean",    [20,50,  50,100, 40,80]),
        ("sunflower",  [30,70,  50,100, 35,75]),
        ("groundnut",  [20,50,  50,100, 40,80]),
    ],
    "MOP": [
        ("potato",     [80,140, 40,80,  80,150]),
        ("banana",     [60,120, 30,70,  80,150]),
        ("tomato",     [60,120, 40,80,  80,150]),
        ("grapes",     [30,70,  30,70,  80,150]),
        ("cotton",     [60,120, 30,70,  80,150]),
        ("tobacco",    [40,90,  30,70,  80,150]),
    ],
    "NPK 10-26-26": [
        ("rice",       [40,90,  60,110, 60,110]),
        ("wheat",      [40,90,  60,110, 60,110]),
        ("maize",      [50,100, 60,110, 60,110]),
        ("cotton",     [50,100, 60,110, 60,110]),
        ("soybean",    [20,60,  60,110, 60,110]),
        ("groundnut",  [20,60,  60,110, 60,110]),
    ],
    "NPK 20-20-20": [
        ("vegetables", [60,120, 60,120, 60,120]),
        ("tomato",     [60,120, 60,120, 60,120]),
        ("chilli",     [50,110, 50,110, 50,110]),
        ("onion",      [50,110, 50,110, 50,110]),
        ("cabbage",    [60,120, 60,120, 60,120]),
        ("cauliflower",[60,120, 60,120, 60,120]),
    ],
    "SSP": [
        ("groundnut",  [20,50,  30,80,  30,70]),
        ("oilseeds",   [20,50,  30,80,  30,70]),
        ("pulses",     [15,45,  30,80,  30,70]),
        ("soybean",    [15,45,  30,80,  30,70]),
        ("sunflower",  [20,50,  30,80,  30,70]),
        ("mustard",    [20,50,  30,80,  30,70]),
    ],
    "Ammonium Sulphate": [
        ("tea",        [80,150, 20,60,  20,60]),
        ("coffee",     [80,150, 20,60,  20,60]),
        ("rice",       [70,130, 20,60,  20,60]),
        ("potato",     [70,130, 25,65,  25,65]),
        ("vegetables", [60,120, 20,60,  20,60]),
        ("sugarcane",  [80,150, 20,60,  20,60]),
    ],
    "Organic Compost": [
        ("all_crops",  [10,60,  10,60,  10,60]),
        ("vegetables", [15,65,  15,65,  15,65]),
        ("fruits",     [10,55,  10,55,  10,55]),
        ("pulses",     [5,40,   10,55,  10,55]),
        ("cereals",    [15,65,  15,65,  15,65]),
        ("spices",     [10,55,  10,55,  10,55]),
    ],
}

SAMPLES_PER_ENTRY = 150
np.random.seed(42)

rows = []
for fertilizer, entries in FERTILIZER_DATA.items():
    for crop, ranges in entries:
        for _ in range(SAMPLES_PER_ENTRY):
            rows.append({
                "N":          np.random.uniform(ranges[0], ranges[1]),
                "P":          np.random.uniform(ranges[2], ranges[3]),
                "K":          np.random.uniform(ranges[4], ranges[5]),
                "crop":       crop,
                "fertilizer": fertilizer,
            })

df = pd.DataFrame(rows)
print(f"Dataset: {len(df)} samples, {df['fertilizer'].nunique()} fertilizers")

le_crop = LabelEncoder()
df["crop_encoded"] = le_crop.fit_transform(df["crop"])

X = df[["N", "P", "K", "crop_encoded"]]
le_fert = LabelEncoder()
y = le_fert.fit_transform(df["fertilizer"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training Random Forest...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)

accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Accuracy: {accuracy * 100:.1f}%")

joblib.dump({
    "model": model,
    "label_encoder_crop": le_crop,
    "label_encoder_fertilizer": le_fert,
    "known_crops": list(le_crop.classes_),
}, OUTPUT_PATH)

print(f"Model saved to {OUTPUT_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_PATH) / 1024:.0f} KB")