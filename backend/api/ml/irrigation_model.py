import os
import logging
import joblib
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, 'api', 'ml', 'irrigation_model.pkl')

_model_data = None


def _load_model():
    global _model_data
    if _model_data is not None:
        return _model_data
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Irrigation model not found at {MODEL_PATH}")
        return None
    try:
        _model_data = joblib.load(MODEL_PATH)
        logger.info("Irrigation recommendation model loaded.")
        return _model_data
    except Exception as e:
        logger.error(f"Failed to load irrigation model: {e}")
        return None


KNOWN_SOILS = [
    "sandy", "loamy", "clay", "silt", "black", "red", "alluvial"
]

KNOWN_CROPS = [
    "rice", "wheat", "maize", "sugarcane", "cotton", "potato",
    "tomato", "onion", "banana", "soybean", "groundnut", "mustard",
    "chilli", "cabbage", "lentil", "chickpea", "millet", "sorghum",
    "barley", "sunflower", "vegetables", "tea", "coffee",
]

# Irrigation schedule details per label
IRRIGATION_DETAILS = {
    "Very Low (2-4 mm/day, every 10-14 days)": {
        "water_per_day": "2–4 mm",
        "frequency": "Every 10–14 days",
        "total_per_week": "14–28 mm",
        "method": "Drip irrigation or rain-fed",
        "best_time": "Early morning (5–7 AM)",
        "tips": [
            "Check soil moisture before each irrigation",
            "Mulching helps retain soil moisture",
            "Rain-fed may be sufficient — monitor closely",
        ],
        "color": "blue",
        "icon": "💧",
    },
    "Low (4-6 mm/day, every 7-10 days)": {
        "water_per_day": "4–6 mm",
        "frequency": "Every 7–10 days",
        "total_per_week": "28–42 mm",
        "method": "Drip or furrow irrigation",
        "best_time": "Early morning (5–7 AM)",
        "tips": [
            "Use soil moisture sensors if available",
            "Avoid waterlogging by checking drainage",
            "Increase frequency during flowering stage",
        ],
        "color": "primary",
        "icon": "💧",
    },
    "Moderate (6-8 mm/day, every 5-7 days)": {
        "water_per_day": "6–8 mm",
        "frequency": "Every 5–7 days",
        "total_per_week": "42–56 mm",
        "method": "Sprinkler or furrow irrigation",
        "best_time": "Early morning (5–8 AM)",
        "tips": [
            "Split irrigation into two sessions for better absorption",
            "Monitor crop for wilting signs",
            "Reduce irrigation during rainy periods",
        ],
        "color": "earth",
        "icon": "💦",
    },
    "High (8-10 mm/day, every 3-5 days)": {
        "water_per_day": "8–10 mm",
        "frequency": "Every 3–5 days",
        "total_per_week": "56–70 mm",
        "method": "Flood or sprinkler irrigation",
        "best_time": "Morning and evening",
        "tips": [
            "Ensure proper drainage to avoid root rot",
            "Check for soil crusting after heavy irrigation",
            "Consider splitting into two daily applications",
        ],
        "color": "earth",
        "icon": "🌊",
    },
    "Very High (10-14 mm/day, every 1-3 days)": {
        "water_per_day": "10–14 mm",
        "frequency": "Every 1–3 days",
        "total_per_week": "70–98 mm",
        "method": "Flood or continuous flow irrigation",
        "best_time": "Multiple times daily if needed",
        "tips": [
            "Maintain standing water for paddy rice",
            "Check bunds and channels daily",
            "High water crops need careful field levelling",
        ],
        "color": "blue",
        "icon": "🌊",
    },
}


def predict_irrigation(crop, soil_type, temperature, humidity, rainfall):
    """
    Predicts irrigation requirement for given crop and conditions.

    Returns:
        dict with success, label, water details, schedule, tips
    """
    model_data = _load_model()
    if model_data is None:
        return {
            'success': False,
            'error': 'Irrigation recommendation model is not available.',
        }

    try:
        model = model_data['model']
        le_soil = model_data['label_encoder_soil']
        le_crop = model_data['label_encoder_crop']
        le_label = model_data['label_encoder_label']
        known_soils = model_data.get('known_soils', KNOWN_SOILS)
        known_crops = model_data.get('known_crops', KNOWN_CROPS)

        # Handle unknown soil
        soil_lower = soil_type.lower().strip()
        unknown_soil = soil_lower not in known_soils
        if unknown_soil:
            soil_lower = 'loamy'

        # Handle unknown crop
        crop_lower = crop.lower().strip()
        unknown_crop = crop_lower not in known_crops
        if unknown_crop:
            crop_lower = 'wheat'

        soil_encoded = le_soil.transform([soil_lower])[0]
        crop_encoded = le_crop.transform([crop_lower])[0]

        features = np.array([[
            temperature, humidity, rainfall,
            soil_encoded, crop_encoded
        ]])

        probabilities = model.predict_proba(features)[0]
        top_idx = int(np.argmax(probabilities))
        top_label = le_label.inverse_transform([top_idx])[0]
        confidence = round(float(probabilities[top_idx]) * 100, 1)

        details = IRRIGATION_DETAILS.get(top_label, {})

        return {
            'success': True,
            'label': top_label,
            'confidence': confidence,
            'water_per_day': details.get('water_per_day', 'N/A'),
            'frequency': details.get('frequency', 'N/A'),
            'total_per_week': details.get('total_per_week', 'N/A'),
            'method': details.get('method', 'N/A'),
            'best_time': details.get('best_time', 'N/A'),
            'tips': details.get('tips', []),
            'icon': details.get('icon', '💧'),
            'unknown_crop': unknown_crop,
            'unknown_soil': unknown_soil,
            'inputs': {
                'crop': crop,
                'soil_type': soil_type,
                'temperature': temperature,
                'humidity': humidity,
                'rainfall': rainfall,
            },
        }

    except Exception as e:
        logger.error(f"Irrigation prediction error: {e}")
        return {'success': False, 'error': str(e)}