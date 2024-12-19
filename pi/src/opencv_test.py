from flask import Flask, Response
import cv2

app = Flask(__name__)

# Open the camera (adjust index if necessary)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

def generate_frames():
    while True:
        # Capture frame-by-frame
        success, frame = cap.read()
        if not success:
            print("Error: Failed to capture frame.")
            break

        # Process the frame
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply edge detection (Canny)
        edges = cv2.Canny(gray_frame, 100, 200)

        # Encode processed frame as JPEG
        ret, buffer = cv2.imencode('.jpg', edges)
        frame = buffer.tobytes()

        # Yield frame for the stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # Route to stream processed frames
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    # Home page
    return "<h1>Edge Detection Stream</h1><img src='/video_feed' width='640'>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)