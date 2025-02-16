import face_recognition
import os

def compare_faces(known_image_path, unknown_image_path):
    print("Comparing faces...")
    print(known_image_path)
    print(unknown_image_path)
    try:
        # Convert relative web paths to absolute file system paths
        base_path = os.path.join(os.getcwd(), "public")  # Assuming images are in public folder
        
        # Remove leading slash and convert to system path
        known_image_path = os.path.join(base_path, known_image_path.lstrip('/'))
        unknown_image_path = os.path.join(base_path, unknown_image_path.lstrip('/'))
        
        # Load and compare images
        known_image = face_recognition.load_image_file(known_image_path)
        unknown_image = face_recognition.load_image_file(unknown_image_path)

        known_encoding = face_recognition.face_encodings(known_image)
        unknown_encoding = face_recognition.face_encodings(unknown_image)

        # Check if faces were detected in both images
        if len(known_encoding) == 0:
            raise Exception("No face detected in the known image, " + known_image_path)
        if len(unknown_encoding) == 0:
            raise Exception("No face detected in the unknown image, " + unknown_image_path)

        # Now we can safely access the first face
        results = face_recognition.compare_faces([known_encoding[0]], unknown_encoding[0])[0]
        return results
        
    except Exception as e:
        print(f"Error in compare_faces: {str(e)}")
        raise e

# print(compare_faces("ID_Images/fakeNandan.jpeg", "ID_Images/idScreenshot.png"))