import face_recognition
import cv2
import numpy as np
from PIL import Image

import cv2
import numpy as np
from ultralytics import YOLO

# download model from https://github.com/akanametov/yolo-face?tab=readme-ov-file, get yolov8n-face.pt
def detect_primary_faces_yolo(image_path, model_path="/Users/derekmiller/Documents/sideproj/IdentityAI/backend/agents/document_agent_helpers/yolov8n-face.pt"):
    """
    Detect the largest face in an image using a YOLO model.

    Args:
        image_path (str): Path to the image file.
        model_path (str): Path to your trained YOLO model (e.g., 'yolov8n-face.pt').

    Returns:
        tuple: (face_location, annotated_image, cropped_face)
               - face_location: (top, right, bottom, left) for the largest detected face
               - annotated_image: copy of the image with bounding box drawn
               - cropped_face: cropped face image (as numpy array)
    """
    # 1. Load the model
    model = YOLO(model_path)  # Load your trained YOLO face model

    # 2. Load and crop the image
    original_image = cv2.imread(image_path)
    if original_image is None:
        raise ValueError(f"Failed to load image from {image_path}")

    image = original_image.copy()

    # 3. Run YOLO prediction
    #    (Ultralytics YOLO automatically handles the resizing,
    #     but you can pass arguments like 'conf=0.25' if needed)
    #    Note: YOLO expects the image in RGB format, so convert as appropriate.
    #    However, passing BGR (as read by cv2) typically still works, but for
    #    best practice we do explicit conversion.
    results = model.predict(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    # 4. Extract face bounding boxes from results
    #    YOLO v8 returns a list of Results objects; for a single image, it's results[0].
    #    Each 'box' has .xyxy, .conf, .cls, etc.
    face_locations = []
    if len(results) > 0 and results[0].boxes is not None:
        for box in results[0].boxes:
            # box.xyxy[0] -> [x1, y1, x2, y2]
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            # Convert float coords to int
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

            # YOLO boxes are (x1, y1, x2, y2)
            # but original code used (top, right, bottom, left)
            top, right, bottom, left = y1, x2, y2, x1
            face_locations.append((top, right, bottom, left))

    # If no faces found, return None
    if not face_locations:
        return None, image, None

    # 5. Find the largest face by area
    largest_face = max(
        face_locations,
        key=lambda face: (face[2] - face[0]) * (face[1] - face[3])
    )

    # 6. Create annotated image and crop the face region
    annotated_image = image.copy()
    padding = 120

    top, right, bottom, left = largest_face
    # Add padding to the bounding box
    padded_top = max(0, top - padding)
    padded_right = min(annotated_image.shape[1], right + padding)
    padded_bottom = min(annotated_image.shape[0], bottom + padding)
    padded_left = max(0, left - padding)

    cropped_face = image[padded_top:padded_bottom, padded_left:padded_right]

    # Draw rectangle on annotated image
    cv2.rectangle(
        annotated_image,
        (padded_left, padded_top),
        (padded_right, padded_bottom),
        (0, 255, 0),
        2,
    )

    # Return same structure as before but with single face
    return largest_face, annotated_image, cropped_face


if __name__ == "__main__":
    image_path = "uploads/IMG_1173.jpeg"
    # image_path = "ID_Images/IMG_9276.jpg"
    largest_face, annotated_image, cropped_face = detect_primary_faces_yolo(image_path)

    # Save the annotated image regardless of face detection
    base_name = image_path.split("/")[-1]
    annotated_path = "annotated_" + base_name
    cv2.imwrite(annotated_path, annotated_image)
    print(f"Annotated image saved to {annotated_path}")

    if largest_face:
        # Save the cropped face
        cropped_path = "cropped_" + base_name
        cv2.imwrite(cropped_path, cropped_face)
        print(f"Face saved to {cropped_path}")
    else:
        print("No faces detected in the image")
        print("No faces detected in the image")
