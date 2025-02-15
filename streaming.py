import cv2
import requests
import json

def stream_webcam():
    # Open a connection to the webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Error: Could not read frame.")
            break

        # Display the resulting frame
        cv2.imshow('Webcam Stream', frame)

        # Check for key presses
        key = cv2.waitKey(1) & 0xFF
        
        # Break the loop on 'q' key press
        if key == ord('q'):
            break
        # Capture frame on spacebar press
        elif key == ord(' '):
            # Convert frame to jpg format
            _, img_encoded = cv2.imencode('.jpg', frame)
            # Convert to bytes
            img_bytes = img_encoded.tobytes()
            
            try:
                # Send the image to the API endpoint
                response = requests.post(
                    'http://localhost:000/api/v1/example',
                    files={'image': ('image.jpg', img_bytes, 'image/jpeg')}
                )
                print(f"Image sent to API. Response: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending image to API: {e}")

    # Release the webcam and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    stream_webcam()
