from anthropic import Anthropic
import base64


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = "ID_Images/IMG_9276.jpg"

# Getting the base64 string
base64_image = encode_image(image_path)

client = Anthropic()

chat_completion = client.messages.create(
    temperature=0,
    system="""
    You are a world-class OCR machine. We are working to distinguish between fake and real IDs. 
    Do not create any new information that is not on the ID itself.""",
    messages=[
        {
          
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please extract the information from this ID in JSON format."
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }
    ],
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000
)

print(chat_completion.content[0].text)