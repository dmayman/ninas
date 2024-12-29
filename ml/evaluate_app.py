import os
import numpy as np
import cv2
import tensorflow as tf
from flask import Flask, render_template, request, redirect, url_for

# Load the TensorFlow Lite model
interpreter = tf.lite.Interpreter(model_path="tm_dog_model/model2.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def load_labels(labels_path):
    """
    Loads class labels from a labels.txt file.
    """
    with open(labels_path, "r") as file:
        return [line.strip() for line in file.readlines()]

# Load class labels from the labels.txt file
labels_path = "tm_dog_model/labels.txt"  # Adjust the path as needed
class_labels = load_labels(labels_path)

# Folder containing test images
TEST_FOLDER = "training_photos/test-photos/test-set-3/"

# Create the Flask app
app = Flask(__name__, static_folder=str(TEST_FOLDER))
app.config["TEST_FOLDER"] = TEST_FOLDER

def preprocess_image(image_path, input_size):
    """
    Preprocesses the input image to match the model's requirements by cropping to a square and resizing.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found at {image_path}")
    
    # Get the dimensions of the image
    height, width, _ = img.shape

    # Determine the size of the square crop (smallest dimension)
    crop_size = min(height, width)

    # Calculate the top-left corner of the crop
    top = 0
    left = 0

    # Crop the image to a square
    cropped_img = img[top:top + crop_size, left:left + crop_size]

    # Resize the cropped image to the input size
    resized_img = cv2.resize(cropped_img, input_size)

    # Ensure pixel values are UINT8 (0-255)
    resized_img = resized_img.astype(np.uint8)

    # Add a batch dimension
    return np.expand_dims(resized_img, axis=0)

def evaluate_image(image_path):
    """
    Evaluates the image using the TensorFlow Lite model.
    """
    input_size = (224, 224)  # Match the input size used during training
    img = preprocess_image(image_path, input_size)

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()

    predictions = interpreter.get_tensor(output_details[0]['index'])[0]

    # Linear map from 0–255 to 0–100
    predictions = predictions / 255.0 * 100.0  # Scale to 0–100

    # Ensure predictions are valid
    predictions = np.nan_to_num(predictions, nan=0.0)  # Replace NaN values with 0
    confidence_scores = {label: float(predictions[i]) for i, label in enumerate(class_labels)}

    return {
        "class": max(confidence_scores, key=confidence_scores.get),  # Top class
        "confidence_scores": confidence_scores
    }

@app.route("/")
def index():
    """
    Displays the images in the test folder grouped by predicted class and sorted by confidence.
    """
    grouped_images = {label: [] for label in class_labels}  # Group images by class
    test_folder_path = os.path.join(app.config["TEST_FOLDER"])

    for filename in os.listdir(test_folder_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(test_folder_path, filename)

            try:
                result = evaluate_image(image_path)
                grouped_images[result["class"]].append({
                    "filename": filename,
                    "confidence_score": result["confidence_scores"][result["class"]],
                    "confidence_scores": result["confidence_scores"]
                })
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Sort images within each class by confidence score (highest first)
    for label in grouped_images:
        grouped_images[label].sort(key=lambda x: x["confidence_score"], reverse=True)

    return render_template("index.html", grouped_images=grouped_images, folder=TEST_FOLDER, class_labels=class_labels)

if __name__ == "__main__":
    app.run(debug=True)