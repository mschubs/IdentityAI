from anthropic import Anthropic
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('secret.env')

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

schema = {
    "observed": {
        # "profileImage": str,
        "name": str,
        "idNumber": str,
        "dateOfBirth": str,
        "expiryDate": str,
        "nationality": str,
        "gender": str
    }
}

stateIDFormats = {
  "Alabama":      ["first+middle", "last"],  # Verified via sample images & user reports
  "Alaska":       ["last", "first+middle"],
  "Arizona":      ["last", "first+middle"],
  "Arkansas":     ["last", "first+middle"],
  "California":   ["first+middle", "last"],  # California DMV: FN = first+middle, LN = last
  "Colorado":     ["last", "first+middle"],
  "Connecticut":  ["last", "first+middle"],
  "Delaware":     ["last", "first+middle"],
  "District of Columbia": ["last", "first+middle"],
  "Florida":      ["last", "first+middle"],
  "Georgia":      ["last", "first+middle"],
  "Hawaii":       ["last", "first+middle"],
  "Idaho":        ["last", "first+middle"],
  "Illinois":     ["last", "first+middle"],
  "Indiana":      ["last", "first+middle"],
  "Iowa":         ["last", "first+middle"],
  "Kansas":       ["last", "first+middle"],
  "Kentucky":     ["last", "first+middle"],
  "Louisiana":    ["last", "first+middle"],
  "Maine":        ["last", "first+middle"],
  "Maryland":     ["last", "first+middle"],
  "Massachusetts":["last", "first+middle"],
  "Michigan":     ["first+middle", "last"],  # Michigan’s new design confirmed on Michigan.gov
  "Minnesota":    ["last", "first+middle"],
  "Mississippi":  ["last", "first+middle"],
  "Missouri":     ["last", "first+middle"],
  "Montana":      ["last", "first+middle"],
  "Nebraska":     ["last", "first+middle"],
  "Nevada":       ["last", "first+middle"],
  "New Hampshire":["last", "first+middle"],
  "New Jersey":   ["last", "first+middle"],
  "New Mexico":   ["last", "first+middle"],
  "New York":     ["last", "first+middle"],
  "North Carolina":["last", "first+middle"],
  "North Dakota": ["last", "first+middle"],
  "Ohio":         ["last", "first+middle"],
  "Oklahoma":     ["last", "first+middle"],
  "Oregon":       ["last", "first+middle"],
  "Pennsylvania": ["last", "first+middle"],
  "Rhode Island": ["last", "first+middle"],
  "South Carolina":["last", "first+middle"],
  "South Dakota": ["last", "first+middle"],
  "Tennessee":    ["last", "first+middle"],
  "Texas":        ["last", "first+middle"],
  "Utah":         ["last", "first+middle"],
  "Vermont":      ["last", "first+middle"],
  "Virginia":     ["last", "first+middle"],
  "Washington":   ["last", "first+middle"],
  "West Virginia":["last", "first+middle"],
  "Wisconsin":    ["last", "first+middle"],
  "Wyoming":      ["last", "first+middle"]
};


# Path to your image
image_path = "ID_Images/IMG_9276.jpg"

# Getting the base64 string
base64_image = encode_image(image_path)

# Initialize client with API key from environment
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

chat_completion = client.messages.create(
    temperature=0,
    system="""
    You are a world-class OCR machine. We are working to distinguish between fake and real IDs. 
    Do not create any new information that is not on the ID itself. 
    Do not add respond with any additional information, only respond with the JSON object.""",
    messages=[
        {
          
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""
                    Please extract the information from this ID into this scheme {schema}. 
                    The ID has some combination of first name, last name and middle name. 
                    Use the state to determine the order of the names in the ID. 
                    The middle name is always on the same line as the first name, 
                    so if you can see two names on one line that must be first name followed by middle name.
                    As a backup, use this dictionary of state to format: {stateIDFormats}
                    Name should be in the format of FirstName MiddleName LastName.
                    """
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