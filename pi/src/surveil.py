import os
import time
import cv2
import json
import datetime
import tflite_runtime.interpreter as tflite
import numpy as np
import subprocess

# Configuration Variables
CONFIDENCE_THRESHOLD = 90  # Confidence in percentage
NUM_FRAMES = 3  # Number of frames to analyze
MOTION_DELAY_MS = 250  # Delay between frames in milliseconds
MOTION_THRESHOLD = 0.01  # Motion area threshold (fraction of total frame size)
JSON_REPORT_PATH = "report/report.json"
REPORT_DATA_DIR = "report/report-data"

# Load TensorFlow Lite model
interpreter = tflite.Interpreter(model_path="dog_singular_model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Class labels
class_labels = ["Mila", "Nova", "None"]

# Ensure report directory exists
os.makedirs(REPORT_DATA_DIR, exist_ok=True)

def preprocess_frame(frame, input_size):
    img = cv2.resize(frame, input_size)
    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, axis=0)

def analyze_frame(frame):
    input_size = (128, 128)
    processed_frame = preprocess_frame(frame, input_size)
    interpreter.set_tensor(input_details[0]['index'], processed_frame)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]
    predicted_class = np.argmax(predictions)
    confidence = predictions[predicted_class] * 100
    return class_labels[predicted_class], confidence

def detect_motion(prev_frame, curr_frame):
    diff = cv2.absdiff(prev_frame, curr_frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    motion_area = cv2.countNonZero(thresh) / float(thresh.size)
    return motion_area > MOTION_THRESHOLD

def append_to_json(file_path, data):
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

def start_web_app():
    """
    Starts the web app as a separate process.
    """
    web_app_path = os.path.abspath("surveil_report_app.py")  # Ensure absolute path
    python_path = os.environ.get("PYTHON_PATH", "python3")  # Use system Python by default

    try:
        subprocess.Popen(
            [python_path, web_app_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(web_app_path)  # Ensure correct working directory
        )
        print("Web app starting...")
    except FileNotFoundError as e:
        print(f"Error: Could not find {web_app_path}. Make sure the file exists.")
    except Exception as e:
        print(f"Error starting the web app: {e}")

def main():
    """
    Main function to detect motion and analyze frames.
    """
    # Start the web app
    start_web_app()

    cap = cv2.VideoCapture(0)  # Use camera 0
    _, prev_frame = cap.read()

    while True:
        _, curr_frame = cap.read()
        if detect_motion(prev_frame, curr_frame):
            print("Motion detected! Capturing frames...")
            captured_frames = []
            for i in range(NUM_FRAMES):
                time.sleep(MOTION_DELAY_MS / 1000.0)
                _, frame = cap.read()
                captured_frames.append(frame)

            # Preprocess frames as a batch
            batch_input = np.vstack([
                preprocess_frame(frame, (128, 128)) for frame in captured_frames
            ])

            # Perform inference in a single model invocation
            interpreter.set_tensor(input_details[0]['index'], batch_input)
            interpreter.invoke()

            # Extract predictions for each frame
            predictions = interpreter.get_tensor(output_details[0]['index'])

            # Process predictions
            results = []
            for i, prediction in enumerate(predictions):
                predicted_class = np.argmax(prediction)
                confidence = prediction[predicted_class] * 100
                results.append((class_labels[predicted_class], confidence, captured_frames[i]))

            # Check consistency across all predictions
            if len(results) == NUM_FRAMES:
                consistent_dog = results[0][0]
                if all(result[0] == consistent_dog for result in results):
                    timestamp = int(time.time())
                    print(f"Consistent detection of {consistent_dog} with {NUM_FRAMES} frames.")

                    report = {
                        "dog": consistent_dog,
                        "timestamp": timestamp,
                        "frames": []
                    }

                    for i, (dog, confidence, frame) in enumerate(results):
                        filename = f"{consistent_dog}_{timestamp}_{i}.jpg"
                        filepath = os.path.join(REPORT_DATA_DIR, filename)
                        cv2.imwrite(filepath, frame)
                        report["frames"].append({
                            "filename": filename,
                            "confidence": confidence,
                        })

                    append_to_json(JSON_REPORT_PATH, report)
                    print(f"Report logged for {consistent_dog}.")

        prev_frame = curr_frame

if __name__ == "__main__":
    main()