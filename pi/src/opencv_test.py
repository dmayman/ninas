from flask import Flask, Response, render_template_string, request
import cv2

app = Flask(__name__)

# Open the camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Define current processing effect
current_effect = "none"

# HTML Template with buttons
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>OpenCV Stream with Effects</title>
</head>
<body>
    <h1>OpenCV Stream with Effects</h1>
    <img src="/video_feed" width="640"><br><br>
    <button onclick="changeEffect('none')">No Effect</button>
    <button onclick="changeEffect('gray')">Grayscale</button>
    <button onclick="changeEffect('edges')">Edge Detection</button>
    <button onclick="changeEffect('blur')">Gaussian Blur</button>
    <button onclick="changeEffect('text')">Text Overlay</button>
    <button onclick="changeEffect('shapes')">Shapes</button>
    <button onclick="changeEffect('faces')">Face Detection</button>
    <script>
        function changeEffect(effect) {
            fetch('/set_effect?effect=' + effect);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Render the main page
    return render_template_string(HTML_TEMPLATE)

@app.route('/set_effect')
def set_effect():
    # Set the current effect based on button click
    global current_effect
    current_effect = request.args.get('effect', 'none')
    return ("", 204)

def generate_frames():
    global current_effect

    while True:
        # Capture frame-by-frame
        success, frame = cap.read()
        if not success:
            break

        # Apply the selected effect
        if current_effect == "gray":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)  # Convert back to BGR for encoding
        elif current_effect == "edges":
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_frame, 50, 150)
            frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        elif current_effect == "blur":
            frame = cv2.GaussianBlur(frame, (15, 15), 0)
        elif current_effect == "text":
            cv2.putText(frame, "OpenCV Stream!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        elif current_effect == "shapes":
            cv2.rectangle(frame, (50, 50), (200, 200), (0, 255, 0), 2)
            cv2.circle(frame, (320, 240), 50, (255, 0, 0), 3)
        elif current_effect == "faces":
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # Route to stream video
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)