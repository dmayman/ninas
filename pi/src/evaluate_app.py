from flask import Flask, render_template, request, redirect, url_for
import os
import numpy as np
import cv2
import tensorflow as tf 

# Load the TensorFlow Lite model
interpreter = tf.lite.Interpreter(model_path="dog_classifier_model_v1.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Class labels
class_labels = ["Mila", "Nova", "None"]

# Folder containing test images
TEST_FOLDER = "test_photos/test-set-2a"

# Create the Flask app
app = Flask(__name__, static_folder=str(TEST_FOLDER))
app.config["TEST_FOLDER"] = TEST_FOLDER

def preprocess_image(image_path, input_size):
    """
    Preprocesses the input image to match the model's requirements.
    """
    # Load the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found at {image_path}")
    
    # Resize the image
    img = cv2.resize(img, input_size)

    # Normalize pixel values to [0, 1]
    img = img.astype(np.float32) / 255.0

    # Add a batch dimension
    img = np.expand_dims(img, axis=0)
    
    return img

def evaluate_image(image_path):
    """
    Evaluates the image using the TensorFlow Lite model.
    """
    input_size = (212, 212)  # Match the input size used during training
    img = preprocess_image(image_path, input_size)

    # Set the input tensor
    interpreter.set_tensor(input_details[0]['index'], img)

    # Run inference
    interpreter.invoke()

    # Get the predictions
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]

    # Find the predicted class and confidence
    predicted_class = np.argmax(predictions)
    confidence = predictions[predicted_class]

    return {
        "class": class_labels[predicted_class],
        "confidence": confidence * 100
    }

@app.route("/")
def index():
    """
    Displays the images in the test folder grouped by predicted class.
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
                    "confidence": result["confidence"]
                })
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    return render_template("evaluate.html", grouped_images=grouped_images, folder=TEST_FOLDER)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)