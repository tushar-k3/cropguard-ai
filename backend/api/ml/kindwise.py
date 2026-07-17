import requests
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

KINDWISE_API_URL = "https://plant.id/api/v3/health_assessment"

# These are the 38 disease classes the PlantVillage dataset covers.
# Used to warn users when the fallback model is likely unreliable.
PLANTVIL_LAGE_CLASSES = [
    "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust",
    "Apple___healthy", "Blueberry___healthy", "Cherry___Powdery_mildew",
    "Cherry___healthy", "Corn___Cercospora_leaf_spot",
    "Corn___Common_rust", "Corn___Northern_Leaf_Blight", "Corn___healthy",
    "Grape___Black_rot", "Grape___Esca", "Grape___Leaf_blight",
    "Grape___healthy", "Orange___Haunglongbing", "Peach___Bacterial_spot",
    "Peach___healthy", "Pepper___Bacterial_spot", "Pepper___healthy",
    "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
    "Raspberry___healthy", "Soybean___healthy", "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch", "Strawberry___healthy",
    "Tomato___Bacterial_spot", "Tomato___Early_blight",
    "Tomato___Late_blight", "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites",
    "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus", "Tomato___healthy",
]


def encode_image_to_base64(image_file):
    """Convert an uploaded image file to base64 string for the API."""
    image_file.seek(0)
    return base64.b64encode(image_file.read()).decode('utf-8')


def call_kindwise(image_file):
    """
    Sends image to Kindwise Plant.id API for health assessment.

    Returns a dict with:
        success (bool)
        source (str): 'kindwise'
        plant_name (str)
        is_healthy (bool)
        diseases (list of dicts)
        error (str) — only if success is False
        limit_exceeded (bool) — True when quota is used up
    """
    api_key = settings.KINDWISE_API_KEY

    if not api_key:
        logger.warning("KINDWISE_API_KEY is not set. Skipping Kindwise call.")
        return {
            'success': False,
            'error': 'Kindwise API key not configured.',
            'limit_exceeded': False,
        }

    try:
        image_b64 = encode_image_to_base64(image_file)

        payload = {
            "images": [f"data:image/jpeg;base64,{image_b64}"],
            "health": "all",
            "classification_level": "species",
        }

        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json",
        }

        response = requests.post(
            KINDWISE_API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        # 429 = rate limit exceeded
        if response.status_code == 429:
            logger.warning("Kindwise API rate limit exceeded.")
            return {
                'success': False,
                'error': 'API limit exceeded.',
                'limit_exceeded': True,
            }

    
        if response.status_code not in (200, 201):
            logger.error(f"Kindwise API error: {response.status_code} — {response.text}")
            return {
                'success': False,
                'error': f"Kindwise API returned status {response.status_code}.",
                'limit_exceeded': False,
        }

        data = response.json()
        return parse_kindwise_response(data)

    except requests.exceptions.Timeout:
        logger.error("Kindwise API request timed out.")
        return {'success': False, 'error': 'Request timed out.', 'limit_exceeded': False}

    except requests.exceptions.ConnectionError:
        logger.error("Cannot reach Kindwise API — no internet connection.")
        return {'success': False, 'error': 'No internet connection.', 'limit_exceeded': False}

    except Exception as e:
        logger.error(f"Unexpected Kindwise error: {e}")
        return {'success': False, 'error': str(e), 'limit_exceeded': False}


def parse_kindwise_response(data):
    """
    Extracts the relevant fields from the Kindwise API response.
    Handles both healthy and diseased plants.
    """
    try:
        result = data.get('result', {})

        # Plant classification
        classification = result.get('classification', {})
        suggestions = classification.get('suggestions', [])
        plant_name = suggestions[0]['name'] if suggestions else 'Unknown Plant'
        plant_probability = suggestions[0].get('probability', 0) if suggestions else 0

        # Health assessment
        is_plant = result.get('is_plant', {}).get('binary', True)
        is_healthy_obj = result.get('is_healthy', {})
        is_healthy = is_healthy_obj.get('binary', True)

        # Disease list
        diseases = []
        disease_suggestions = result.get('disease', {}).get('suggestions', [])

        for disease in disease_suggestions[:5]:  # Top 5 diseases max
            probability = disease.get('probability', 0)
            if probability < 0.05:  # Skip very low probability items
                continue

            disease_details = disease.get('details', {})
            treatments = disease_details.get('treatment', {})

            diseases.append({
                'name': disease.get('name', 'Unknown'),
                'probability': round(probability * 100, 1),
                'description': disease_details.get('description', ''),
                'treatment': {
                    'biological': treatments.get('biological', []),
                    'chemical': treatments.get('chemical', []),
                    'prevention': treatments.get('prevention', []),
                },
                'common_names': disease_details.get('common_names', []),
            })

        return {
            'success': True,
            'source': 'kindwise',
            'is_plant': is_plant,
            'plant_name': plant_name,
            'plant_probability': round(plant_probability * 100, 1),
            'is_healthy': is_healthy,
            'diseases': diseases,
            'limit_exceeded': False,
        }

    except Exception as e:
        logger.error(f"Error parsing Kindwise response: {e}")
        return {
            'success': False,
            'error': f'Failed to parse API response: {e}',
            'limit_exceeded': False,
        }