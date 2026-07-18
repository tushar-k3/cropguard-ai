import os
import logging
import joblib
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, 'api', 'ml', 'fertilizer_model.pkl')

_model_data = None


def _load_model():
    global _model_data
    if _model_data is not None:
        return _model_data
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Fertilizer model not found at {MODEL_PATH}")
        return None
    try:
        _model_data = joblib.load(MODEL_PATH)
        logger.info("Fertilizer recommendation model loaded.")
        return _model_data
    except Exception as e:
        logger.error(f"Failed to load fertilizer model: {e}")
        return None


# Detailed info for each fertilizer
FERTILIZER_INFO = {
    "Urea": {
        "icon": "🧪",
        "nutrient": "46% Nitrogen",
        "best_for": "Nitrogen-deficient soils, leafy growth stage",
        "application": "Broadcast or band application before irrigation",
        "dosage": "100–200 kg/ha depending on crop",
        "caution": "Do not apply near seeds. Split application recommended.",
        "color": "blue",
    },
    "DAP": {
        "icon": "💊",
        "nutrient": "18% N, 46% P₂O₅",
        "best_for": "Phosphorus-deficient soils, root development",
        "application": "Basal application at sowing time",
        "dosage": "50–150 kg/ha",
        "caution": "Avoid mixing with alkaline fertilizers.",
        "color": "earth",
    },
    "MOP": {
        "icon": "🔴",
        "nutrient": "60% K₂O",
        "best_for": "Potassium-deficient soils, fruit quality",
        "application": "Mix into soil before planting or top dress",
        "dosage": "50–100 kg/ha",
        "caution": "Avoid excess application on light sandy soils.",
        "color": "primary",
    },
    "NPK 10-26-26": {
        "icon": "⚗️",
        "nutrient": "10% N, 26% P₂O₅, 26% K₂O",
        "best_for": "Balanced nutrition for cereal and oilseed crops",
        "application": "Basal dose at sowing",
        "dosage": "100–200 kg/ha",
        "caution": "Follow up with nitrogen top dressing.",
        "color": "primary",
    },
    "NPK 20-20-20": {
        "icon": "🌿",
        "nutrient": "20% N, 20% P₂O₅, 20% K₂O",
        "best_for": "Vegetable crops requiring balanced nutrition",
        "application": "Fertigation or foliar spray",
        "dosage": "5–10 kg/ha for foliar; 50–100 kg/ha soil application",
        "caution": "Best used as a supplement, not primary fertilizer.",
        "color": "primary",
    },
    "SSP": {
        "icon": "🟡",
        "nutrient": "16% P₂O₅, 11% Sulphur",
        "best_for": "Oilseeds and pulses, sulphur-deficient soils",
        "application": "Basal application mixed into soil",
        "dosage": "150–250 kg/ha",
        "caution": "Store in dry conditions to prevent caking.",
        "color": "earth",
    },
    "Ammonium Sulphate": {
        "icon": "🔵",
        "nutrient": "21% N, 24% Sulphur",
        "best_for": "Alkaline soils, crops requiring sulphur",
        "application": "Top dressing or basal application",
        "dosage": "100–200 kg/ha",
        "caution": "Acidifies soil — avoid on already acidic soils.",
        "color": "blue",
    },
    "Organic Compost": {
        "icon": "🌱",
        "nutrient": "Variable N, P, K + micronutrients",
        "best_for": "Soil health improvement, all crop types",
        "application": "Incorporate into soil 2–3 weeks before sowing",
        "dosage": "5–10 tonnes/ha",
        "caution": "Ensure compost is fully decomposed before use.",
        "color": "primary",
    },
}

KNOWN_CROPS = [
    "rice", "wheat", "maize", "sugarcane", "cotton", "jute",
    "soybean", "sunflower", "groundnut", "potato", "banana",
    "tomato", "grapes", "tobacco", "vegetables", "chilli",
    "onion", "cabbage", "cauliflower", "oilseeds", "pulses",
    "mustard", "tea", "coffee", "fruits", "cereals", "spices",
    "all_crops",
]


def predict_fertilizer(N, P, K, crop):
    """
    Predicts the best fertilizer for given soil nutrients and crop.

    Returns:
        dict with success, fertilizer, info, top_3, inputs
    """
    model_data = _load_model()
    if model_data is None:
        return {
            'success': False,
            'error': 'Fertilizer recommendation model is not available.',
        }

    try:
        model = model_data['model']
        le_crop = model_data['label_encoder_crop']
        le_fert = model_data['label_encoder_fertilizer']
        known_crops = model_data.get('known_crops', KNOWN_CROPS)

        # Handle unknown crop — use 'all_crops' as fallback
        crop_lower = crop.lower().strip()
        unknown_crop = False

        if crop_lower not in known_crops:
            logger.warning(f"Unknown crop '{crop}' — using 'all_crops' fallback.")
            crop_lower = 'all_crops'
            unknown_crop = True

        crop_encoded = le_crop.transform([crop_lower])[0]
        features = np.array([[N, P, K, crop_encoded]])

        probabilities = model.predict_proba(features)[0]
        top_idx = int(np.argmax(probabilities))
        top_fertilizer = le_fert.inverse_transform([top_idx])[0]
        top_confidence = round(float(probabilities[top_idx]) * 100, 1)

        # Top 3
        top3_indices = np.argsort(probabilities)[::-1][:3]
        top_3 = [
            {
                'fertilizer': le_fert.inverse_transform([int(i)])[0],
                'confidence': round(float(probabilities[i]) * 100, 1),
                'icon': FERTILIZER_INFO.get(
                    le_fert.inverse_transform([int(i)])[0], {}
                ).get('icon', '🧪'),
            }
            for i in top3_indices
        ]

        info = FERTILIZER_INFO.get(top_fertilizer, {
            'icon': '🧪',
            'nutrient': 'N/A',
            'best_for': 'General use',
            'application': 'Follow manufacturer instructions',
            'dosage': 'As recommended',
            'caution': 'Read label before use',
            'color': 'primary',
        })

        return {
            'success': True,
            'fertilizer': top_fertilizer,
            'confidence': top_confidence,
            'icon': info['icon'],
            'nutrient': info['nutrient'],
            'best_for': info['best_for'],
            'application': info['application'],
            'dosage': info['dosage'],
            'caution': info['caution'],
            'top_3': top_3,
            'unknown_crop': unknown_crop,
            'inputs': {
                'N': N, 'P': P, 'K': K, 'crop': crop,
            },
        }

    except Exception as e:
        logger.error(f"Fertilizer prediction error: {e}")
        return {'success': False, 'error': str(e)}