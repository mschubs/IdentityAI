import json
import uuid
from typing import Dict, Any, Optional, Tuple

from anthropic import Anthropic
import base64
import os
from dotenv import load_dotenv
import cv2
import json
from document_agent_helpers.face_detection import detect_primary_faces

class DocumentParsingAgent:
    """
    Agent responsible for extracting and parsing text fields from the ID image.
    """
    
    def __init__(self):
        """Initialize the DocumentParsingAgent with necessary configurations."""
        load_dotenv('secret.env')
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.schema = {
            "observed": {
                "profileImage": str,
                "name": str,
                "address-line-1": str,
                "address-line-2": str,
                "dateOfBirth": str,
                "expiryDate": str,
                "nationality": str,
                "gender": str
            }
        }
        self.stateIDFormats = {
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
            "Michigan":     ["first+middle", "last"],  # Michigan's new design confirmed on Michigan.gov
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
            }

    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def parse_id_document(self, image_path) -> Dict[str, str]:
        """
        Parses an ID image and returns structured data.

        Args:
            id_image (bytes): Binary content of the ID image.

        Returns:
            Dict[str, str]: A dictionary containing ID fields.
        """
        # Process face detection first
        # _, _, cropped_faces, id_card_image = detect_primary_faces(image_path)
        _, _, cropped_faces = detect_primary_faces(image_path)
        
        # Save cropped face if detected
        cropped_IRL_image_path = None
        cropped_ID_image_path = None
        if cropped_faces is not None:
            base_name = image_path.split('/')[-1]
            cropped_IRL_image_path = "cropped_IRL_" + base_name
            cv2.imwrite(cropped_IRL_image_path, cv2.cvtColor(cropped_faces[0], cv2.COLOR_RGB2BGR))
            cropped_ID_image_path = "cropped_ID_" + base_name
            cv2.imwrite(cropped_ID_image_path, cv2.cvtColor(cropped_faces[1], cv2.COLOR_RGB2BGR))

        # Use id_card_image if available, otherwise use original image
        image_to_encode = image_path
        # if id_card_image is not None:
        #     # Save the ID card image temporarily
        #     base_name = image_path.split('/')[-1]
        #     temp_id_path = "temp_id_" + base_name
        #     cv2.imwrite(temp_id_path, cv2.cvtColor(id_card_image, cv2.COLOR_RGB2BGR))
        #     image_to_encode = temp_id_path

        # Getting the base64 string
        base64_image = self.encode_image(image_to_encode)

        # # Clean up temporary file if it was created
        # if id_card_image is not None:
        #     os.remove(temp_id_path)

        # Initialize client with API key from environment
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        chat_completion = client.messages.create(
            temperature=0,
            system="""
            You are a specialized OCR system for ID verification. Focus on:
            1. Exact text extraction without inference
            We are working to distinguish between fake and real IDs. 
            Do not create any NEW INFORMATION that is not on the ID itself. 
            Do not add respond with any additional information, only respond with the JSON object.""",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
                            Please extract the information from this ID into this scheme {self.schema}. 
                            The ID has some combination of first name, last name and middle name. 
                            Use the state to determine the order of the names in the ID. 
                            The middle name is always on the same line as the first name, 
                            so if you can see two names on one line that must be first name followed by middle name.
                            As a backup, use this dictionary of state to format: {self.stateIDFormats}
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

        result = chat_completion.content[0].text

        # Add the profile image path to the result if face was detected
        result_dict = json.loads(result)
        result_dict['observed']['profileImage'] = cropped_IRL_image_path if cropped_IRL_image_path else ""
        # result_dict['observed']['capturedImage'] = cropped_ID_image_path if cropped_ID_image_path else ""
        return json.dumps(result_dict, indent=2)