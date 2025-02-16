import face_recognition
import cv2
import numpy as np

def detect_primary_face(image_path, upsample=1, model='hog'):
    """
    Detect only the primary face in an image, focusing on the largest or most prominent face.
    
    Args:
        image_path (str): Path to the image file
        upsample (int): Number of times to upsample the image
        model (str): Detection model to use - 'hog' or 'cnn'
    
    Returns:
        tuple: (primary_face_location, annotated_image, cropped_face)
    """
    # Load and convert the image
    image = face_recognition.load_image_file(image_path)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect all faces
    face_locations = face_recognition.face_locations(
        rgb_image,
        number_of_times_to_upsample=upsample,
        model=model
    )
    
    # If no faces found, return None
    if not face_locations:
        return None, image, None
    
    # Find the largest face by area
    primary_face = max(face_locations, key=lambda face: 
        (face[2] - face[0]) * (face[1] - face[3])  # area = height * width
    )
    
    # Create annotated image and crop the face region
    annotated_image = image.copy()
    top, right, bottom, left = primary_face
    
    # Add padding to the bounding box (20 pixels on all sides)
    padding = 120
    top = max(0, top - padding)
    right = min(annotated_image.shape[1], right + padding)
    bottom = min(annotated_image.shape[0], bottom + padding)
    left = max(0, left - padding)
    
    cropped_face = image[top:bottom, left:right]
    
    cv2.rectangle(annotated_image, (left, top), (right, bottom), (0, 255, 0), 2)
    
    return primary_face, annotated_image, cropped_face

if __name__ == "__main__":
    image_path = "ID_Images/IMG_9276.jpg"
    primary_face, annotated_image, cropped_face = detect_primary_face(image_path)
    
    if primary_face:
        # Save both the annotated image and the cropped face
        base_name = image_path.split('/')[-1]
        annotated_path = "annotated_" + base_name
        cropped_path = "cropped_" + base_name
        
        cv2.imwrite(annotated_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(cropped_path, cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR))
        print(f"Primary face detected and saved to {annotated_path}")
        print(f"Cropped face saved to {cropped_path}")
    else:
        print("No faces detected in the image")