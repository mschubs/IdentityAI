import face_recognition
import os
import numpy as np
import math

class FaceVerificationAgent:
    def __init__(self, threshold=0.6):
        """
        Initializes the FaceVerificationAgent with a threshold for distance-based confidence.
        
        :param threshold: A float indicating the distance threshold used for l2_to_percent.
        """
        self.threshold = threshold

    def _l2_to_percent(self, distance):
        """
        Converts the L2 distance between two face embeddings into a confidence percentage.
        
        :param distance: The L2 distance between embeddings.
        :return: A float representing confidence (0-100).
        """
        if distance > self.threshold:
            # Non-linear decay for values above threshold
            linear_val = (1.0 - distance) / (self.threshold * 2.0)
            return max(0.0, linear_val * 100)
        else:
            # Enhanced confidence for values below threshold
            adjusted = 1.0 - (distance / (self.threshold * 2.0))
            confidence = adjusted + ((1.0 - adjusted) *
                                    math.pow((adjusted - 0.5) * 2, 0.2))
            return min(100.0, confidence * 100)

    def _compare_face_encodings(self, known_encoding, unknown_encoding):
        """
        Calculates the confidence score by comparing two face encodings.

        :param known_encoding: The face encoding for the known image (list/array).
        :param unknown_encoding: The face encoding for the unknown image (list/array).
        :return: A float representing the confidence percentage (0-100).
        """
        distance = np.linalg.norm(np.array(known_encoding) - np.array(unknown_encoding))
        return self._l2_to_percent(distance)

    def compare_faces(self, known_image_path, unknown_image_path):
        """
        Loads two images from disk, extracts face encodings, and compares them.
        Returns a confidence score from 0 to 100.

        :param known_image_path: Relative or absolute path to the known image.
        :param unknown_image_path: Relative or absolute path to the unknown image.
        :return: A float representing the confidence score (0-100).
        """
        print("Comparing faces...")
        print(known_image_path)
        print(unknown_image_path)
        try:
            # Convert relative web paths to absolute file system paths.
            base_path = os.path.join(os.getcwd(), "public")  # Assuming images are in 'public' folder

            # Remove leading slash and convert to system path
            known_image_path_full = os.path.join(base_path, known_image_path.lstrip('/'))
            unknown_image_path_full = os.path.join(base_path, unknown_image_path.lstrip('/'))

            # Load and compare images
            known_image = face_recognition.load_image_file(known_image_path_full)
            unknown_image = face_recognition.load_image_file(unknown_image_path_full)

            known_encoding = face_recognition.face_encodings(known_image)
            unknown_encoding = face_recognition.face_encodings(unknown_image)

            # Check if faces were detected in both images
            if len(known_encoding) == 0:
                raise Exception("No face detected in the known image, " + known_image_path_full)
            if len(unknown_encoding) == 0:
                raise Exception("No face detected in the unknown image, " + unknown_image_path_full)

            # Compare the first face in each image
            results = self._compare_face_encodings(known_encoding[0], unknown_encoding[0])
            return results

        except Exception as e:
            print(f"Error in compare_faces: {str(e)}")
            raise e

# from face_verification_agent import FaceVerificationAgent

def verify_faces():
    agent = FaceVerificationAgent(threshold=0.6)
    score = agent.compare_faces("ID_Images/fakeNandan.jpeg", "ID_Images/idScreenshot.png")
    print(f"Face match confidence: {score}%")
    return score

if __name__ == "__main__":
    verify_faces()