"""
Builds a MobileNetV2 model with ImageNet pretrained weights
reshaped for 38 PlantVillage classes.

This model has NOT been fine-tuned on plant disease data.
It serves only as a structural fallback — results will show
a warning to the user indicating limited accuracy.

Run from the backend/ folder with venv active:
    python scripts/build_fallback_model.py
"""
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Loading TensorFlow... (this takes 10-30 seconds)")
import keras

NUM_CLASSES = 38
OUTPUT_PATH = "api/ml/mobilenet_plant.h5"

print("Building MobileNetV2 model...")

base_model = keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights='imagenet',
    pooling='avg',
)
base_model.trainable = False

inputs = keras.Input(shape=(224, 224, 3))
x = base_model(inputs, training=False)
x = keras.layers.Dropout(0.2)(x)
outputs = keras.layers.Dense(NUM_CLASSES, activation='softmax')(x)

model = keras.Model(inputs, outputs)

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print(f"Model built. Parameters: {model.count_params():,}")
print(f"Saving to {OUTPUT_PATH}...")

model.save(OUTPUT_PATH)

print(f"Done. File size: {os.path.getsize(OUTPUT_PATH) / 1024 / 1024:.1f} MB")
print()
print("NOTE: This model uses ImageNet weights only.")
print("It has not been trained on plant disease data.")
print("Users will see a warning when this fallback is used.")
