import face_recognition
import cv2
import numpy as np
from PIL import Image

def detect_primary_faces(image_path, upsample=1, model='hog'):
    """
    Detect the two largest faces in an image.
    
    Args:
        image_path (str): Path to the image file
        upsample (int): Number of times to upsample the image
        model (str): Detection model to use - 'hog' or 'cnn'
    
    Returns:
        tuple: (face_locations, annotated_image, cropped_faces)
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
    
    # Sort faces by area (largest to smallest)
    sorted_faces = sorted(face_locations, 
                         key=lambda face: (face[2] - face[0]) * (face[1] - face[3]),
                         reverse=True)
    
    # Get the two largest faces (or just one if that's all we have)
    primary_faces = sorted_faces[:2]
    
    # Create annotated image and crop the face regions
    annotated_image = image.copy()
    cropped_faces = []
    padding = 120
    
    for face in primary_faces:
        top, right, bottom, left = face
        
        # Add padding to the bounding box
        padded_top = max(0, top - padding)
        padded_right = min(annotated_image.shape[1], right + padding)
        padded_bottom = min(annotated_image.shape[0], bottom + padding)
        padded_left = max(0, left - padding)
        
        cropped_face = image[padded_top:padded_bottom, padded_left:padded_right]
        cropped_faces.append(cropped_face)
        
        cv2.rectangle(annotated_image, (padded_left, padded_top), 
                     (padded_right, padded_bottom), (0, 255, 0), 2)
    
    # id_card_image = None
    # # Create additional wide crop of second face if it exists
    # if len(primary_faces) > 1:
    #     face = primary_faces[1]
    #     top, right, bottom, left = face
    #     wide_padding_h = 700  # horizontal padding
    #     wide_padding_v = 300  # vertical padding
        
    #     # Add increased padding to the bounding box
    #     wide_top = max(0, top - wide_padding_v)
    #     wide_right = min(annotated_image.shape[1], right + wide_padding_h)
    #     wide_bottom = min(annotated_image.shape[0], bottom + wide_padding_v)
    #     wide_left = max(0, left - wide_padding_h)
        
    #     id_card_image = image[wide_top:wide_bottom, wide_left:wide_right]
    #     # Save the wide cropped face separately
    #     base_name = image_path.split('/')[-1]
    #     wide_cropped_path = "wide_cropped_" + base_name
    #     cv2.imwrite(wide_cropped_path, cv2.cvtColor(id_card_image, cv2.COLOR_RGB2BGR))
    #     print(f"Wide cropped face saved to {wide_cropped_path}")

    return primary_faces, annotated_image, cropped_faces

if __name__ == "__main__":
    image_path = "ID_Images/Nandan+ID.jpeg"
    # image_path = "ID_Images/IMG_9276.jpg"
    primary_faces, annotated_image, cropped_faces, id_card_image = detect_primary_faces(image_path)
    
    # Save the annotated image regardless of face detection
    base_name = image_path.split('/')[-1]
    annotated_path = "annotated_" + base_name
    cv2.imwrite(annotated_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
    print(f"Annotated image saved to {annotated_path}")
    
    if primary_faces:
        # Save each cropped face with a different index
        for i, face in enumerate(cropped_faces):
            cropped_path = f"cropped_{i+1}_" + base_name
            cv2.imwrite(cropped_path, cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
            print(f"Face {i+1} saved to {cropped_path}")
    else:
        print("No faces detected in the image")