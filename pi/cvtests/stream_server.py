from flask import Flask, Response
import cv2

app = Flask(__name__)

# Open the camera (adjust index if necessary)
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FPS, 15)

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
    # Home page
    return "<h1>Camera Stream</h1><img src='/video_feed' width='640'>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)