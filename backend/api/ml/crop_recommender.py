import os
import logging
import joblib
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, 'api', 'ml', 'crop_model.pkl')

_payload = None


def _load_model():
    global _payload
    if _payload is not None:
        return _payload
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Crop model not found at {MODEL_PATH}")
        return None
    try:
        _payload = joblib.load(MODEL_PATH)
        logger.info("Crop recommendation model loaded.")
        return _payload
    except Exception as e:
        logger.error(f"Failed to load crop model: {e}")
        return None


# Crop details shown to the user after recommendation
CROP_DETAILS = {
    "rice":        {"emoji": "🌾", "season": "Kharif", "duration": "3-6 months"},
    "maize":       {"emoji": "🌽", "season": "Kharif / Rabi", "duration": "3-4 months"},
    "chickpea":    {"emoji": "🫘", "season": "Rabi", "duration": "3-4 months"},
    "kidneybeans": {"emoji": "🫘", "season": "Kharif", "duration": "3-4 months"},
    "pigeonpeas":  {"emoji": "🫘", "season": "Kharif", "duration": "6-9 months"},
    "mothbeans":   {"emoji": "🫘", "season": "Kharif", "duration": "2-3 months"},
    "mungbean":    {"emoji": "🫘", "season": "Kharif / Zaid", "duration": "2-3 months"},
    "blackgram":   {"emoji": "🫘", "season": "Kharif", "duration": "3 months"},
    "lentil":      {"emoji": "🫘", "season": "Rabi", "duration": "4-5 months"},
    "pomegranate": {"emoji": "🍎", "season": "Perennial", "duration": "5-7 months"},
    "banana":      {"emoji": "🍌", "season": "Perennial", "duration": "12-15 months"},
    "mango":       {"emoji": "🥭", "season": "Perennial", "duration": "3-5 months"},
    "grapes":      {"emoji": "🍇", "season": "Perennial", "duration": "2-3 months"},
    "watermelon":  {"emoji": "🍉", "season": "Zaid / Kharif", "duration": "2-3 months"},
    "muskmelon":   {"emoji": "🍈", "season": "Zaid", "duration": "2-3 months"},
    "apple":       {"emoji": "🍎", "season": "Perennial", "duration": "4-5 months"},
    "orange":      {"emoji": "🍊", "season": "Perennial", "duration": "8-10 months"},
    "papaya":      {"emoji": "🍈", "season": "Perennial", "duration": "9-12 months"},
    "coconut":     {"emoji": "🥥", "season": "Perennial", "duration": "12 months"},
    "cotton":      {"emoji": "🌿", "season": "Kharif", "duration": "5-6 months"},
    "jute":        {"emoji": "🌿", "season": "Kharif", "duration": "4-5 months"},
    "coffee":      {"emoji": "☕", "season": "Perennial", "duration": "9-11 months"},
}


def recommend_crop(nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall):
    """
    Predicts the best crop for the given soil and climate conditions.

    Returns a dict with:
        success (bool)
        crop (str)
        confidence (float)
        top_3 (list) — top 3 predictions with probabilities
        details (dict) — season, duration, emoji
    """
    payload = _load_model()

    if payload is None:
        return {
            'success': False,
            'error': 'Crop recommendation model is not available.',
        }

    try:
        model = payload['model']
        encoder = payload['encoder']

        features = np.array([[
            float(nitrogen),
            float(phosphorus),
            float(potassium),
            float(temperature),
            float(humidity),
            float(ph),
            float(rainfall),
        ]])

        # Get probabilities for all classes
        probabilities = model.predict_proba(features)[0]
        top_indices = np.argsort(probabilities)[::-1][:3]

        predicted_index = top_indices[0]
        predicted_crop = encoder.inverse_transform([predicted_index])[0]
        confidence = float(probabilities[predicted_index]) * 100

        top_3 = []
        for idx in top_indices:
            crop_name = encoder.inverse_transform([idx])[0]
            top_3.append({
                'crop': crop_name,
                'confidence': round(float(probabilities[idx]) * 100, 1),
                'emoji': CROP_DETAILS.get(crop_name, {}).get('emoji', '🌱'),
            })

        details = CROP_DETAILS.get(predicted_crop, {
            'emoji': '🌱',
            'season': 'Unknown',
            'duration': 'Unknown',
        })

        return {
            'success': True,
            'crop': predicted_crop,
            'confidence': round(confidence, 1),
            'top_3': top_3,
            'details': details,
        }

    except Exception as e:
        logger.error(f"Crop recommendation error: {e}")
        return {
            'success': False,
            'error': f'Prediction failed: {e}',
        }