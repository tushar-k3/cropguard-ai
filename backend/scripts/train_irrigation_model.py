"""
Trains a Random Forest classifier for irrigation recommendation.
Run from backend/ folder with venv active:
    python scripts/train_irrigation_model.py
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
OUTPUT_PATH = "api/ml/irrigation_model.pkl"

# Irrigation categories
# [water_req_mm_per_day, frequency_days, label]
IRRIGATION_LABELS = {
    "Very Low (2-4 mm/day, every 10-14 days)":  (3,  12),
    "Low (4-6 mm/day, every 7-10 days)":         (5,  8),
    "Moderate (6-8 mm/day, every 5-7 days)":     (7,  6),
    "High (8-10 mm/day, every 3-5 days)":        (9,  4),
    "Very High (10-14 mm/day, every 1-3 days)":  (12, 2),
}

# Crop water demand categories
CROP_WATER_NEEDS = {
    "low":       ["chickpea", "lentil", "mustard", "groundnut", "millet", "sorghum", "barley"],
    "moderate":  ["wheat", "maize", "cotton", "soybean", "sunflower", "potato", "onion"],
    "high":      ["rice", "sugarcane", "banana", "vegetables", "tomato", "chilli", "cabbage"],
    "very_high": ["sugarcane", "rice", "banana", "tea", "coffee"],
}

SOIL_WATER_RETENTION = {
    "sandy":    0.3,
    "loamy":    0.6,
    "clay":     0.8,
    "silt":     0.7,
    "black":    0.75,
    "red":      0.5,
    "alluvial": 0.65,
}

SAMPLES = 300
np.random.seed(42)
rows = []

for _ in range(SAMPLES * 10):
    temp = np.random.uniform(15, 45)
    humidity = np.random.uniform(20, 95)
    rainfall = np.random.uniform(0, 300)
    soil_type = np.random.choice(list(SOIL_WATER_RETENTION.keys()))
    retention = SOIL_WATER_RETENTION[soil_type]

    crop_category = np.random.choice(["low", "moderate", "high", "very_high"])
    crop = np.random.choice(CROP_WATER_NEEDS[crop_category])

    # Calculate water need score
    temp_factor    = (temp - 15) / 30
    humidity_factor = 1 - (humidity / 100)
    rain_factor    = max(0, 1 - (rainfall / 200))
    soil_factor    = 1 - retention

    crop_weights = {"low": 0.2, "moderate": 0.5, "high": 0.75, "very_high": 1.0}
    crop_weight  = crop_weights[crop_category]

    score = (
        temp_factor    * 0.30 +
        humidity_factor * 0.25 +
        rain_factor    * 0.25 +
        soil_factor    * 0.10 +
        crop_weight    * 0.10
    )

    if score < 0.25:
        label = "Very Low (2-4 mm/day, every 10-14 days)"
    elif score < 0.42:
        label = "Low (4-6 mm/day, every 7-10 days)"
    elif score < 0.58:
        label = "Moderate (6-8 mm/day, every 5-7 days)"
    elif score < 0.75:
        label = "High (8-10 mm/day, every 3-5 days)"
    else:
        label = "Very High (10-14 mm/day, every 1-3 days)"

    rows.append({
        "temperature": temp,
        "humidity": humidity,
        "rainfall": rainfall,
        "soil_type": soil_type,
        "crop": crop,
        "label": label,
    })

df = pd.DataFrame(rows)
print(f"Dataset: {len(df)} samples, {df['label'].nunique()} irrigation levels")

le_soil = LabelEncoder()
le_crop = LabelEncoder()
df["soil_encoded"] = le_soil.fit_transform(df["soil_type"])
df["crop_encoded"] = le_crop.fit_transform(df["crop"])

X = df[["temperature", "humidity", "rainfall", "soil_encoded", "crop_encoded"]]
le_label = LabelEncoder()
y = le_label.fit_transform(df["label"])

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
    "label_encoder_soil": le_soil,
    "label_encoder_crop": le_crop,
    "label_encoder_label": le_label,
    "known_soils": list(le_soil.classes_),
    "known_crops": list(le_crop.classes_),
}, OUTPUT_PATH)

print(f"Model saved to {OUTPUT_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_PATH) / 1024:.0f} KB")