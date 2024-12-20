from flask import Flask, Response
import cv2

app = Flask(__name__)

# Open the camera (adjust index if necessary)
camera = cv2.VideoCapture(0)

def adjust_white_balance(frame):
    """
    Adjust the white balance of the frame using LAB color space.
    """
    # Convert the frame to LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    # Split LAB channels
    l, a, b = cv2.split(lab)

    # Adjust A and B channels to reduce color tint
    a = cv2.add(a, 10)  # Fine-tune these values to reduce pink tones
    b = cv2.subtract(b, 10)

    # Merge the LAB channels and convert back to BGR
    corrected_lab = cv2.merge((l, a, b))
    corrected_frame = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)

    return corrected_frame

def generate_frames():
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()
        if not success:
            break
        else:
            # Apply white balance adjustment
            frame = adjust_white_balance(frame)

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