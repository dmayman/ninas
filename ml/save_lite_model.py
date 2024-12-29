import tensorflow as tf
from PIL import Image
import numpy as np
import os

# Load the HDF5 model
model = tf.keras.models.load_model("dog_singular_model.keras")

# Representative dataset function
dataset_path = "training_photos/singular_square"
img_height, img_width = 128, 128

def representative_dataset():
    for class_folder in os.listdir(dataset_path):
        class_folder_path = os.path.join(dataset_path, class_folder)
        if not os.path.isdir(class_folder_path):
            continue
        for image_file in os.listdir(class_folder_path):
            image_path = os.path.join(class_folder_path, image_file)
            try:
                img = Image.open(image_path).convert("RGB")
                img = img.resize((img_width, img_height))
                img = np.array(img).astype(np.float32) / 255.0
                yield [np.expand_dims(img, axis=0)]
            except Exception as e:
                print(f"Error processing image {image_path}: {e}")

# Convert the model with 8-bit quantization
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.uint8
converter.inference_output_type = tf.uint8

# Convert the model
tflite_model = converter.convert()

# Save the quantized model
with open("dog_classifier_model_quantized.tflite", "wb") as f:
    f.write(tflite_model)

print("Model successfully converted with calibration.")