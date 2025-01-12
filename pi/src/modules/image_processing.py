import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from modules.state import app_state as state
from config import MODEL_PATH, INPUT_SIZE, CLASS_LABELS, VERIFY_TIMES, MOTION_THRESHOLD
from modules.logger import logger

# Initialize TensorFlow Lite model
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Detect motion between two frames
def detect_motion(prev_frame, curr_frame):
    diff = cv2.absdiff(prev_frame, curr_frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    motion_area = cv2.countNonZero(thresh) / float(thresh.size)
    return motion_area > MOTION_THRESHOLD

def preprocess_image(img, input_size):
    """
    Preprocesses the input image to match the model's requirements by cropping to a square and resizing.
    """
    height, width, _ = img.shape
    crop_size = min(height, width)  # Square crop size (smallest dimension)
    cropped_img = img[0:crop_size, 0:crop_size]  # Crop to a square
    resized_img = cv2.resize(cropped_img, input_size).astype(np.uint8)  # Resize and convert to uint8
    return np.expand_dims(resized_img, axis=0)  # Add batch dimension

def evaluate_frames():
    """
    Evaluates the image using the TensorFlow Lite model and returns the averaged confidence scores.
    """
    last_top_class = None
    confidence_sums = {label: 0.0 for label in CLASS_LABELS}  # Sum of confidence scores for averaging
    confidence_averages = {label: 0.0 for label in CLASS_LABELS}  # Averaged confidence scores

    for idx in range(VERIFY_TIMES):
        logger.debug(f"Evaluating frame {idx}...")
        
        _, state.curr_frame = state.cap.read() if idx else (None, state.curr_frame)  # Read a new frame if idx > 0
        img = preprocess_image(state.curr_frame, INPUT_SIZE)  # Preprocess image
        interpreter.set_tensor(input_details[0]['index'], img)  # Set input tensor
        interpreter.invoke()  # Run inference
        predictions = interpreter.get_tensor(output_details[0]['index'])[0]  # Get model output

        # Scale predictions from 0-255 to 0-100%
        predictions = predictions / 255.0 * 100.0
        predictions = np.nan_to_num(predictions, nan=0.0)  # Replace NaN with 0 if any

        # Incremental sum of confidence scores
        for i, label in enumerate(CLASS_LABELS):
            confidence_sums[label] += predictions[i]  # Add to the running sum

        # Calculate the running average
        num_cycles = idx + 1  # Calculate the current number of cycles
        for label in CLASS_LABELS:
            confidence_averages[label] = confidence_sums[label] / num_cycles

        top_class = max(confidence_averages, key=confidence_averages.get)  # Class with the highest average confidence

        # Check if the detected class is unstable
        if last_top_class and top_class != last_top_class:
            logger.info(f"Detected class instability: Changed from {last_top_class} to {top_class}. Ending evaluation.")
            break

        last_top_class = top_class  # Update last top class

    return {
        "class": last_top_class,  # Final detected class
        "confidence_scores": confidence_averages  # Averaged confidence scores for all classes
    }