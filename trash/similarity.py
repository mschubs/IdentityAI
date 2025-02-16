import face_recognition

def compare_faces(known_image, unknown_image):
    known_image = face_recognition.load_image_file(known_image)
    unknown_image = face_recognition.load_image_file(unknown_image)

    known_encoding = face_recognition.face_encodings(known_image)[0]
    unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

    results = face_recognition.compare_faces([known_encoding], unknown_encoding)[0]
    return results

print(compare_faces("ID_Images/fakeNandan.jpeg", "ID_Images/idScreenshot.png"))