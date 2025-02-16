from google.cloud import vision

client = vision.ImageAnnotatorClient()
image_path = "text_image.png"

with open(image_path, "rb") as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.text_detection(image=image)

print(response.text_annotations[0].description)  # Extracted text

