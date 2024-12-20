from flask import Flask, Response, jsonify
import cv2
from gpiozero import DistanceSensor

app = Flask(__name__)

# Open the camera (adjust index if necessary)
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FPS, 15)

# Initialize the ultrasonic sensor
# Replace TRIG and ECHO with the GPIO pins you are using
TRIG = 4
ECHO = 17
sensor = DistanceSensor(echo=ECHO, trigger=TRIG)

def generate_frames():
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Yield frame to the web browser
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # Route to stream the camera feed
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    # Home page with distance reading
    return """
        <h1>Camera Stream</h1>
        <p id="distance">Current Distance: Loading...</p>
        <img src='/video_feed' width='640'>
        <script>
            async function updateDistance() {
                const response = await fetch('/distance');
                const data = await response.json();
                document.getElementById('distance').innerText = `Current Distance: ${data.distance.toFixed(2)} cm`;
            }
            setInterval(updateDistance, 1000); // Update every second
        </script>
    """

@app.route('/distance')
def get_distance():
    # Return the current distance as JSON
    current_distance = sensor.distance * 100  # Convert to cm
    return jsonify({"distance": current_distance})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)