import cv2
import numpy as np
import mss

# Define the region of the screen where the livestream appears.
# Adjust these values (top, left, width, height) to match your screen.
monitor = {"top": 100, "left": 100, "width": 800, "height": 600}

with mss.mss() as sct:
    while True:
        # Capture the region defined in 'monitor'
        screenshot = sct.grab(monitor)
        # Convert the raw data to a NumPy array
        frame = np.array(screenshot)
        # Convert from BGRA to BGR (OpenCV uses BGR color order)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # At this point, 'frame' is the current image of your livestream.
        # You can now run your object detection model on this frame.
        
        # For demonstration, we'll simply display the frame.
        cv2.imshow("Livestream Capture", frame)
        
        # Press 'q' to exit.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cv2.destroyAllWindows()