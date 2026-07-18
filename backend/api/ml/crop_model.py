import os
import logging
import joblib
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, 'api', 'ml', 'crop_model.pkl')

_model_data = None


def _load_model():
    global _model_data
    if _model_data is not None:
        return _model_data
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Crop model not found at {MODEL_PATH}")
        return None
    try:
        _model_data = joblib.load(MODEL_PATH)
        logger.info("Crop recommendation model loaded.")
        return _model_data
    except Exception as e:
        logger.error(f"Failed to load crop model: {e}")
        return None


# Crop-specific advice shown alongside the recommendation
CROP_INFO = {
    "rice":        {"season": "Kharif", "duration": "120-150 days", "icon": "🌾"},
    "wheat":       {"season": "Rabi",   "duration": "100-120 days", "icon": "🌾"},
    "maize":       {"season": "Kharif", "duration": "90-120 days",  "icon": "🌽"},
    "chickpea":    {"season": "Rabi",   "duration": "90-120 days",  "icon": "🫘"},
    "kidneybeans": {"season": "Kharif", "duration": "90-120 days",  "icon": "🫘"},
    "pigeonpeas":  {"season": "Kharif", "duration": "150-180 days", "icon": "🫘"},
    "mothbeans":   {"season": "Kharif", "duration": "60-90 days",   "icon": "🫘"},
    "mungbean":    {"season": "Kharif", "duration": "60-90 days",   "icon": "🫘"},
    "blackgram":   {"season": "Kharif", "duration": "60-90 days",   "icon": "🫘"},
    "lentil":      {"season": "Rabi",   "duration": "100-120 days", "icon": "🫘"},
    "pomegranate": {"season": "Annual", "duration": "150-180 days", "icon": "🍎"},
    "banana":      {"season": "Annual", "duration": "270-365 days", "icon": "🍌"},
    "mango":       {"season": "Summer", "duration": "3-5 years",    "icon": "🥭"},
    "grapes":      {"season": "Annual", "duration": "2-3 years",    "icon": "🍇"},
    "watermelon":  {"season": "Zaid",   "duration": "80-110 days",  "icon": "🍉"},
    "muskmelon":   {"season": "Zaid",   "duration": "75-100 days",  "icon": "🍈"},
    "apple":       {"season": "Winter", "duration": "4-5 years",    "icon": "🍎"},
    "orange":      {"season": "Winter", "duration": "3-5 years",    "icon": "🍊"},
    "papaya":      {"season": "Annual", "duration": "270-300 days", "icon": "🍈"},
    "coconut":     {"season": "Annual", "duration": "5-7 years",    "icon": "🥥"},
    "cotton":      {"season": "Kharif", "duration": "150-180 days", "icon": "🌿"},
    "jute":        {"season": "Kharif", "duration": "100-120 days", "icon": "🌿"},
    "coffee":      {"season": "Annual", "duration": "3-4 years",    "icon": "☕"},
}


def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
    """
    Predicts the best crop for given soil and climate parameters.

    Returns:
        dict with success, crop, confidence, top_3, crop_info
    """
    model_data = _load_model()
    if model_data is None:
        return {
            'success': False,
            'error': 'Crop recommendation model is not available.',
        }

    try:
        model = model_data['model']
        le = model_data['label_encoder']

        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        probabilities = model.predict_proba(features)[0]

        # Top prediction
        top_idx = int(np.argmax(probabilities))
        top_crop = le.inverse_transform([top_idx])[0]
        top_confidence = round(float(probabilities[top_idx]) * 100, 1)

        # Top 3 predictions
        top3_indices = np.argsort(probabilities)[::-1][:3]
        top_3 = [
            {
                'crop': le.inverse_transform([int(i)])[0],
                'confidence': round(float(probabilities[i]) * 100, 1),
                'icon': CROP_INFO.get(
                    le.inverse_transform([int(i)])[0], {}
                ).get('icon', '🌱'),
            }
            for i in top3_indices
        ]

        info = CROP_INFO.get(top_crop, {
            'season': 'Unknown',
            'duration': 'Unknown',
            'icon': '🌱',
        })

        return {
            'success': True,
            'crop': top_crop,
            'confidence': top_confidence,
            'icon': info['icon'],
            'season': info['season'],
            'duration': info['duration'],
            'top_3': top_3,
            'inputs': {
                'N': N, 'P': P, 'K': K,
                'temperature': temperature,
                'humidity': humidity,
                'ph': ph,
                'rainfall': rainfall,
            },
        }

    except Exception as e:
        logger.error(f"Crop prediction error: {e}")
        return {'success': False, 'error': str(e)}