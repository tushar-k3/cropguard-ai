import os
import logging
import numpy as np
from PIL import Image
from django.conf import settings

logger = logging.getLogger(__name__)

# Path where the model weights will be stored.
# On free-tier deployments with ephemeral filesystems, this file
# will not persist across restarts — documented limitation.
MODEL_PATH = os.path.join(settings.BASE_DIR, 'api', 'ml', 'mobilenet_plant.h5')

# PlantVillage class labels in the order the model outputs them
CLASS_LABELS = [
    "Apple - Apple Scab", "Apple - Black Rot", "Apple - Cedar Apple Rust",
    "Apple - Healthy", "Blueberry - Healthy", "Cherry - Powdery Mildew",
    "Cherry - Healthy", "Corn - Cercospora Leaf Spot", "Corn - Common Rust",
    "Corn - Northern Leaf Blight", "Corn - Healthy", "Grape - Black Rot",
    "Grape - Esca (Black Measles)", "Grape - Leaf Blight", "Grape - Healthy",
    "Orange - Huanglongbing (Citrus Greening)", "Peach - Bacterial Spot",
    "Peach - Healthy", "Pepper - Bacterial Spot", "Pepper - Healthy",
    "Potato - Early Blight", "Potato - Late Blight", "Potato - Healthy",
    "Raspberry - Healthy", "Soybean - Healthy", "Squash - Powdery Mildew",
    "Strawberry - Leaf Scorch", "Strawberry - Healthy",
    "Tomato - Bacterial Spot", "Tomato - Early Blight",
    "Tomato - Late Blight", "Tomato - Leaf Mold",
    "Tomato - Septoria Leaf Spot", "Tomato - Spider Mites",
    "Tomato - Target Spot", "Tomato - Yellow Leaf Curl Virus",
    "Tomato - Mosaic Virus", "Tomato - Healthy",
]

# Which labels indicate the plant is healthy
HEALTHY_LABELS = {label for label in CLASS_LABELS if 'Healthy' in label}

# Crops supported by the PlantVillage dataset
SUPPORTED_CROPS = {
    'apple', 'blueberry', 'cherry', 'corn', 'grape', 'orange',
    'peach', 'pepper', 'potato', 'raspberry', 'soybean',
    'squash', 'strawberry', 'tomato',
}

_model = None  # Module-level cache so model loads only once per server start


def _load_model():
    """
    Loads the MobileNetV2 model from disk.
    Returns None if the model file does not exist.
    The model file must be downloaded separately — see README.
    """
    global _model

    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        logger.warning(
            f"Fallback model not found at {MODEL_PATH}. "
            "Fallback detection will not be available until the model is downloaded."
        )
        return None

    try:
        # Import here so TensorFlow only loads when actually needed
        import tensorflow as tf
        _model = tf.keras.models.load_model(MODEL_PATH)
        logger.info("MobileNetV2 fallback model loaded successfully.")
        return _model
    except Exception as e:
        logger.error(f"Failed to load fallback model: {e}")
        return None


def preprocess_image(image_file):
    """
    Resizes and normalizes the image for MobileNetV2 input.
    MobileNetV2 expects: (224, 224, 3) float32 in [-1, 1] range.
    """
    image_file.seek(0)
    img = Image.open(image_file).convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    # Normalize to [-1, 1] as MobileNetV2 was pretrained
    img_array = (img_array / 127.5) - 1.0
    return np.expand_dims(img_array, axis=0)


def is_supported_crop(predicted_label):
    """
    Checks if the predicted label matches a crop in the PlantVillage dataset.
    Returns False for any plant not in the training data.
    """
    label_lower = predicted_label.lower()
    return any(crop in label_lower for crop in SUPPORTED_CROPS)


def run_fallback(image_file):
    """
    Runs MobileNetV2 inference on the image.

    Returns a dict with:
        success (bool)
        source (str): 'local_model'
        plant_name (str)
        is_healthy (bool)
        diseases (list)
        unsupported_crop (bool) — True if outside PlantVillage dataset
        model_available (bool) — False if model file is missing
        warning (str) — shown to user when results may be unreliable
    """
    model = _load_model()

    if model is None:
        return {
            'success': False,
            'source': 'local_model',
            'model_available': False,
            'error': (
                'The offline fallback model is not installed. '
                'Please contact support or try again when internet is available.'
            ),
        }

    try:
        img_array = preprocess_image(image_file)
        predictions = model.predict(img_array, verbose=0)
        predicted_index = int(np.argmax(predictions[0]))
        confidence = float(np.max(predictions[0])) * 100

        predicted_label = CLASS_LABELS[predicted_index]
        is_healthy = predicted_label in HEALTHY_LABELS
        supported = is_supported_crop(predicted_label)

        # Extract crop name and disease name from label
        parts = predicted_label.split(' - ', 1)
        plant_name = parts[0] if len(parts) > 1 else predicted_label
        disease_name = parts[1] if len(parts) > 1 else predicted_label

        diseases = []
        warning = None

        if not supported:
            # Plant is outside the training dataset
            warning = (
                "This plant is outside the supported crop dataset. "
                "The result may not be accurate. "
                "Please use the Kindwise-powered scan when internet is available."
            )
        elif not is_healthy:
            diseases = [{
                'name': disease_name,
                'probability': round(confidence, 1),
                'description': (
                    f"Detected by offline model with {confidence:.1f}% confidence. "
                    "Verify with the AI-powered scan for treatment details."
                ),
                'treatment': {
                    'biological': [],
                    'chemical': [],
                    'prevention': [
                        'Verify this diagnosis with the Kindwise AI scan for detailed treatment options.'
                    ],
                },
                'common_names': [],
            }]

        return {
            'success': True,
            'source': 'local_model',
            'model_available': True,
            'is_plant': True,
            'plant_name': plant_name,
            'plant_probability': round(confidence, 1),
            'is_healthy': is_healthy,
            'diseases': diseases,
            'unsupported_crop': not supported,
            'warning': warning,
        }

    except Exception as e:
        logger.error(f"Fallback model inference error: {e}")
        return {
            'success': False,
            'source': 'local_model',
            'model_available': True,
            'error': f'Inference failed: {e}',
        }