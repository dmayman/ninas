import cv2
import torch
from flask import Flask, Response
import numpy as np

# Load YOLO model (using YOLOv5 from Ultralytics)
model = torch.hub.load('ultralytics/yolov5', 'yolov5n')  # Small YOLOv5 model

# Open the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

def calculate_distance(box_height, frame_height):
    """
    Estimate distance based on bounding box height relative to frame height.
    Adjust the scale factor based on your testing and dog's average size.
    """
    known_height = 0.5  # Approximate average dog height in meters
    focal_length = 500  # Focal length in pixels (calibrate for your camera)
    distance = (focal_length * known_height) / box_height
    return distance

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        # Perform detection
        results = model(frame)
        detections = results.xyxy[0].cpu().numpy()  # Extract bounding boxes

        for detection in detections:
            x1, y1, x2, y2, confidence, cls = detection
            label = model.names[int(cls)]

            if label == "dog" and confidence > 0.5:  # Filter for dogs with confidence > 50%
                # Draw bounding box and label
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                box_height = int(y2) - int(y1)
                frame_height = frame.shape[0]

                # Calculate distance
                distance = calculate_distance(box_height, frame_height)

                # Display distance
                cv2.putText(frame, f"Dog: {int(distance)}m", (int(x1), int(y1) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield frame for the stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Flask server
app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Dog Detection Stream</h1><img src='/video_feed' width='640'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)