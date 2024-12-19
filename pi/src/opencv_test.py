import cv2

# Open the camera (adjust index if necessary)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Press 'q' to quit.")

try:
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Process the frame
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        

        # Apply edge detection (Canny)
        edges = cv2.Canny(gray_frame, 100, 200)

        # Display original and processed frames
        cv2.imshow('Original', frame)
        cv2.imshow('Edges', edges)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released.")