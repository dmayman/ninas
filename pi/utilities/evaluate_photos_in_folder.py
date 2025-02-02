import tensorflow.lite.Interpreter as tflite
import numpy as np
import cv2
import os

# Configurations
MODEL_PATH = "../src/tm_dog_model/model3.tflite"  # Path to your TensorFlow Lite model
CLASS_LABELS = ["Mila", "Nova", "None"]  # Class names in the model
INPUT_SIZE = (224, 224)  # Adjust to match your model's expected input size

# Load the TensorFlow Lite model
interpreter = tflite(MODEL_PATH)
interpreter.allocate_tensors()

# Get input and output tensors
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_image(image_path):
    """Loads and preprocesses an image for TensorFlow Lite model inference."""
    image = cv2.imread(image_path)
    if image is None:
        return None
    image = cv2.resize(image, INPUT_SIZE)
    image = np.expand_dims(image, axis=0).astype(np.float32) / 255.0  # Normalize
    return image

def evaluate_image(image_path):
    """Runs inference on an image and returns the predicted class."""
    image = preprocess_image(image_path)
    if image is None:
        return None, None

    interpreter.set_tensor(input_details[0]['index'], image)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]  # Extract predictions

    # Convert predictions to percentages and get the predicted class
    predictions = predictions / 255.0 * 100.0
    predicted_index = np.argmax(predictions)
    predicted_class = CLASS_LABELS[predicted_index]

    return predicted_class, predictions

def main():
    """Main function to evaluate images and find mismatched classifications."""
    # Step 1: Ask for the expected class
    while True:
        chosen_class = input(f"Enter the correct class ({', '.join(CLASS_LABELS)}): ").strip()
        if chosen_class in CLASS_LABELS:
            break
        print("Invalid class! Please enter one of:", ", ".join(CLASS_LABELS))

    # Step 2: Ask for the folder path
    while True:
        folder_path = input("Enter the folder path containing images: ").strip()
        if os.path.isdir(folder_path):
            break
        print("Invalid folder path! Please enter a valid directory.")

    mismatched_images = []

    print(f"\nEvaluating images in '{folder_path}' for class '{chosen_class}'...\n")
    for filename in os.listdir(folder_path):
        image_path = os.path.join(folder_path, filename)
        predicted_class, confidence_scores = evaluate_image(image_path)

        if predicted_class is None:
            print(f"Skipping {filename} (could not load image)")
            continue

        if predicted_class != chosen_class:
            mismatched_images.append(filename)

    # Print mismatched images
    print("\n=== Mismatched Images ===")
    if mismatched_images:
        for img in mismatched_images:
            print(img)
    else:
        print("All images matched the chosen class.")

if __name__ == "__main__":
    main()