import os
import time
import numpy as np
import cv2
import tflite_runtime.interpreter as tflite

# Load the TensorFlow Lite model
interpreter = tflite.Interpreter(model_path="dog_classifier_model_v1.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Class labels
class_labels = ["Mila", "Nova", "None"]

def preprocess_image(image_path, input_size):
    """
    Preprocesses the input image to match the model's requirements.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found at {image_path}")
    
    # Resize the image to match the model's input size
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

    # Measure inference time
    start_time = time.time()
    interpreter.invoke()
    inference_time = time.time() - start_time

    # Get the predictions
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]

    # Find the predicted class and confidence
    predicted_class = np.argmax(predictions)
    confidence = predictions[predicted_class]

    return {
        "class": class_labels[predicted_class],
        "confidence": confidence * 100,
        "time": inference_time
    }

def main():
    """
    Main function to prompt the user for an image path and evaluate it.
    """
    while True:
        image_path = input("Enter the relative path to the image (or 'exit' to quit): ").strip()
        if image_path.lower() == "exit":
            print("Exiting...")
            break

        # Check if the file exists
        if not os.path.isfile(image_path):
            print(f"Error: File not found at {image_path}. Please try again.")
            continue

        try:
            # Evaluate the image
            result = evaluate_image(image_path)
            print(f"Class: {result['class']}")
            print(f"Confidence: {result['confidence']:.2f}%")
            print(f"Time Spent Evaluating: {result['time']:.4f} seconds")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()