import cv2

# Open the camera (0 for the default camera)
cap = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Capturing an image...")

try:
    # Capture a single frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
    else:
        # Save the captured frame as an image file
        filename = "captured_image.jpg"
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")
finally:
    # Release the camera
    cap.release()
    print("Camera released.")