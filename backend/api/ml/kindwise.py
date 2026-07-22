import requests
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

KINDWISE_HEALTH_URL = "https://plant.id/api/v3/health_assessment"
PLANTNET_API_URL    = "https://my-api.plantnet.org/v2/identify/all"

NON_PLANT_WORDS = {
    'nutrient deficiency', 'deficiency', 'stress', 'damage',
    'injury', 'disorder', 'abiotic', 'unknown', 'other',
    'mechanical damage', 'frost damage', 'sunburn', 'waterlogging',
}

COMMON_PLANTS = [
    'Tomato', 'Potato', 'Apple', 'Corn', 'Grape', 'Cherry',
    'Peach', 'Pepper', 'Strawberry', 'Soybean', 'Wheat',
    'Rice', 'Cotton', 'Sugarcane', 'Banana', 'Mango',
    'Onion', 'Chilli', 'Citrus', 'Orange', 'Maize',
    'Cauliflower', 'Cabbage', 'Brinjal', 'Okra', 'Pea',
    'Groundnut', 'Sunflower', 'Mustard', 'Lentil', 'Chickpea',
    'Pomegranate', 'Guava', 'Papaya', 'Coconut', 'Turmeric',
]


def encode_image(image_file):
    image_file.seek(0)
    return base64.b64encode(image_file.read()).decode('utf-8')


def identify_via_plantnet(image_file):
    """
    Uses Pl@ntNet API to identify plant species.
    Free tier: 500 requests/day.
    Returns (common_name, scientific_name, confidence_percent)
    """
    plantnet_key = getattr(settings, 'PLANTNET_API_KEY', '')
    if not plantnet_key:
        logger.warning("PLANTNET_API_KEY not set.")
        return '', '', 0

    try:
        image_file.seek(0)
        files  = [('images', ('plant.jpg', image_file, 'image/jpeg'))]
        params = {
            'api-key':    plantnet_key,
            'include-related-images': 'false',
            'no-reject':  'false',
            'lang':       'en',
        }

        response = requests.post(
            PLANTNET_API_URL,
            files=files,
            params=params,
            timeout=20,
        )

        if response.status_code == 404:
            # PlantNet returns 404 when it cannot identify the plant
            logger.info("PlantNet: plant not recognized in image.")
            return '', '', 0

        if response.status_code != 200:
            logger.warning(f"PlantNet returned {response.status_code}: {response.text[:200]}")
            return '', '', 0

        data    = response.json()
        results = data.get('results', [])

        if not results:
            return '', '', 0

        top         = results[0]
        score       = top.get('score', 0)
        species     = top.get('species', {})
        sci_name    = species.get('scientificNameWithoutAuthor', '')
        common_names = species.get('commonNames', [])
        common_name  = common_names[0] if common_names else ''

        # Use common name if available, otherwise use scientific name
        display_name = common_name or sci_name

        if display_name and display_name.lower() not in NON_PLANT_WORDS:
            # Capitalize properly
            display_name = display_name.title()
            confidence   = round(score * 100, 1)
            logger.info(
                f"PlantNet identified: {display_name} "
                f"(sci: {sci_name}) at {confidence}%"
            )
            return display_name, sci_name, confidence

        return '', sci_name, 0

    except Exception as e:
        logger.warning(f"PlantNet identification failed: {e}")
        return '', '', 0


def infer_plant_from_disease(diseases_raw):
    """Infer plant name from disease name as last resort."""
    for disease in diseases_raw[:3]:
        d_name = disease.get('name', '')
        for plant in COMMON_PLANTS:
            if plant.lower() in d_name.lower():
                return plant
    return ''


def call_kindwise(image_file):
    """
    Main detection function.

    Plant name strategy:
    1. PlantNet API (free, 500/day, 75k+ species) ← primary
    2. Infer from disease name ← fallback
    3. 'Unknown Plant' ← last resort

    Disease detection:
    - Kindwise health assessment API ← unchanged
    """
    kindwise_key = settings.KINDWISE_API_KEY
    if not kindwise_key:
        return {
            'success':        False,
            'error':          'Kindwise API key not configured.',
            'limit_exceeded': False,
        }

    try:
        # ── Step 1: Identify plant via PlantNet ─────────────────────────────
        common_name, sci_name, plant_probability = identify_via_plantnet(image_file)
        plant_name = common_name
        logger.info(f"PlantNet result: '{plant_name}' ({plant_probability}%)")

        # ── Step 2: Disease detection via Kindwise ───────────────────────────
        image_b64 = encode_image(image_file)
        health_payload = {
            "images":               [f"data:image/jpeg;base64,{image_b64}"],
            "health":               "all",
            "classification_level": "species",
        }
        headers = {
            "Api-Key":      kindwise_key,
            "Content-Type": "application/json",
        }
        health_response = requests.post(
            KINDWISE_HEALTH_URL,
            json=health_payload,
            headers=headers,
            timeout=30,
        )

        if health_response.status_code == 429:
            return {
                'success':        False,
                'error':          'Kindwise API limit exceeded.',
                'limit_exceeded': True,
            }

        if health_response.status_code not in (200, 201):
            return {
                'success':        False,
                'error':          f"Kindwise returned {health_response.status_code}.",
                'limit_exceeded': False,
            }

        health_data  = health_response.json()
        result       = health_data.get('result', {})
        is_plant     = result.get('is_plant',   {}).get('binary', True)
        is_healthy   = result.get('is_healthy', {}).get('binary', True)
        diseases_raw = result.get('disease', {}).get('suggestions', [])

        # ── Step 3: Fallback plant name from disease if PlantNet failed ──────
        if not plant_name:
            plant_name = infer_plant_from_disease(diseases_raw)
            if plant_name:
                logger.info(f"Inferred plant from disease: '{plant_name}'")

        if not plant_name or plant_name.lower() in NON_PLANT_WORDS:
            # Use scientific name if we have it
            if sci_name:
                plant_name = sci_name.title()
            else:
                plant_name = 'Unknown Plant'

        # ── Step 4: Build disease list ───────────────────────────────────────
        diseases = []
        for disease in diseases_raw[:5]:
            probability  = disease.get('probability', 0)
            disease_name = disease.get('name', '')

            if probability < 0.05:
                continue
            if disease_name.lower() in NON_PLANT_WORDS:
                continue

            disease_details = disease.get('details', {})
            treatments      = disease_details.get('treatment', {})

            diseases.append({
                'name':         disease_name,
                'probability':  round(probability * 100, 1),
                'description':  disease_details.get('description', ''),
                'treatment': {
                    'biological': treatments.get('biological', []),
                    'chemical':   treatments.get('chemical', []),
                    'prevention': treatments.get('prevention', []),
                },
                'common_names': disease_details.get('common_names', []),
            })

        return {
            'success':              True,
            'source':               'kindwise',
            'is_plant':             is_plant,
            'plant_name':           plant_name,
            'scientific_name':      sci_name,
            'plant_probability':    plant_probability,
            'is_healthy':           is_healthy,
            'diseases':             diseases,
            'limit_exceeded':       False,
        }

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out.', 'limit_exceeded': False}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'No internet connection.', 'limit_exceeded': False}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {'success': False, 'error': str(e), 'limit_exceeded': False}