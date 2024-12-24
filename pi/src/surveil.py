import os
import time
import cv2
import json
import datetime
import tflite_runtime.interpreter as tflite
import numpy as np

# Configuration Variables
CONFIDENCE_THRESHOLD = 95  # Confidence in percentage
NUM_FRAMES = 3  # Number of frames to analyze
MOTION_DELAY_MS = 250  # Delay between frames in milliseconds
MOTION_THRESHOLD = 0.1  # Motion area threshold (fraction of total frame size)
JSON_REPORT_PATH = "report/report.json"
REPORT_DATA_DIR = "report/report-data"

# Load TensorFlow Lite model
interpreter = tflite.Interpreter(model_path="dog_classifier_model_v1.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Class labels
class_labels = ["Mila", "Nova", "None"]

# Ensure report directory exists
os.makedirs(REPORT_DATA_DIR, exist_ok=True)

def preprocess_frame(frame, input_size):
    """
    Preprocesses a frame for TensorFlow Lite model inference.
    """
    img = cv2.resize(frame, input_size)
    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, axis=0)

def analyze_frame(frame):
    """
    Runs the TensorFlow Lite model on a single frame.
    """
    input_size = (212, 212)  # Match model input size
    processed_frame = preprocess_frame(frame, input_size)
    interpreter.set_tensor(input_details[0]['index'], processed_frame)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]
    predicted_class = np.argmax(predictions)
    confidence = predictions[predicted_class] * 100
    return class_labels[predicted_class], confidence

def detect_motion(prev_frame, curr_frame):
    """
    Detects motion by comparing two frames.
    """
    diff = cv2.absdiff(prev_frame, curr_frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    motion_area = cv2.countNonZero(thresh) / float(thresh.size)
    return motion_area > MOTION_THRESHOLD

def append_to_json(file_path, data):
    """
    Appends data to a JSON file atomically.
    """
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump([], f)

    with open(file_path, "r") as f:
        reports = json.load(f)

    reports.append(data)

    temp_path = f"{file_path}.tmp"
    with open(temp_path, "w") as f:
        json.dump(reports, f, indent=4)
    os.replace(temp_path, file_path)

def main():
    """
    Main function to detect motion and analyze frames.
    """
    cap = cv2.VideoCapture(0)  # Use camera 0
    _, prev_frame = cap.read()

    while True:
        _, curr_frame = cap.read()
        if detect_motion(prev_frame, curr_frame):
            print("Motion detected! Analyzing frames...")
            captured_frames = []
            for i in range(NUM_FRAMES):
                time.sleep(MOTION_DELAY_MS / 1000.0)  # Small delay between frames
                _, frame = cap.read()
                captured_frames.append(frame)

            results = []
            for frame in captured_frames:
                dog, confidence = analyze_frame(frame)
                if confidence >= CONFIDENCE_THRESHOLD:
                    results.append((dog, confidence, frame))

            if len(results) == NUM_FRAMES:
                consistent_dog = results[0][0]  # Check if all predictions are consistent
                if all(result[0] == consistent_dog for result in results):
                    timestamp = datetime.datetime.now()
                    timestamp_readable = timestamp.strftime("%b %d %Y, %I:%M%p")
                    timestamp_relative = f"{int(time.time() - timestamp.timestamp()) // 60}m ago"

                    print(f"Consistent detection of {consistent_dog} with {NUM_FRAMES} frames.")
                    
                    report = {
                        "dog": consistent_dog,
                        "timestamp": {
                            "absolute": timestamp_readable,
                            "relative": timestamp_relative,
                        },
                        "frames": []
                    }

                    for i, (dog, confidence, frame) in enumerate(results):
                        filename = os.path.join(REPORT_DATA_DIR, f"{consistent_dog}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{i}.jpg")
                        cv2.imwrite(filename, frame)
                        report["frames"].append({
                            "filename": filename,
                            "confidence": confidence,
                        })

                    append_to_json(JSON_REPORT_PATH, report)
                    print(f"Report logged for {consistent_dog}.")

        prev_frame = curr_frame

if __name__ == "__main__":
    main()