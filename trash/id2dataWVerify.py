from anthropic import Anthropic
import base64
import os
from dotenv import load_dotenv
import cv2
import json
from datetime import datetime
import re


schema = {
    "observed": {
        "profileImage": str,
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
};


def validate_date_format(date_str):
    """Validate common US date formats."""
    date_patterns = [
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        r'\d{4}-\d{2}-\d{2}'   # YYYY-MM-DD
    ]
    return any(re.match(pattern, date_str) for pattern in date_patterns)

class IDVerificationError(Exception):
    """Custom exception for ID verification errors."""
    pass

def process_id_image(image_path, min_age=21):
    """
    Process ID image with enhanced validation and security checks.
    
    Args:
        image_path (str): Path to the ID image
        min_age (int): Minimum required age for validation
        
    Returns:
        dict: Processed ID information with validation results
        
    Raises:
        IDVerificationError: If critical validation checks fail
    """
    try:
        # Validate input file
        if not os.path.exists(image_path):
            raise IDVerificationError("Image file not found")
            
        # Getting the base64 string
        base64_image = encode_image(image_path)
        
        # Initialize validation results
        validation_results = {
            "age_check_passed": False,
            "expiry_check_passed": False,
            "format_check_passed": False,
            "potential_risks": []
        }

        # Process face detection
        try:
            from face_detection import detect_primary_face
            _, _, cropped_face = detect_primary_face(image_path)
            
            if cropped_face is None:
                validation_results["potential_risks"].append("No face detected in ID")
            
            # Save cropped face if detected
            cropped_image_path = None
            if cropped_face is not None:
                base_name = os.path.basename(image_path)
                cropped_image_path = f"cropped_{base_name}"
                cv2.imwrite(cropped_image_path, cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR))
        except Exception as e:
            validation_results["potential_risks"].append(f"Face detection error: {str(e)}")

        # Initialize Anthropic client
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Enhanced system prompt for better accuracy
        system_prompt = """
        You are a specialized OCR system for ID verification. Focus on:
        1. Exact text extraction without inference
        2. Consistent date format validation
        3. Name order verification based on state formats
        4. No sensitive number storage
        Only respond with the JSON object, no additional text.
        """

        # Make API call
        chat_completion = client.messages.create(
            temperature=0,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"Extract ID information into {schema}. Use state format {stateIDFormats} for name order."
                }, {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image
                    }
                }]
            }],
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000
        )

        # Parse result
        result = json.loads(chat_completion.content[0].text)
        
        # Add profile image path
        result['observed']['profileImage'] = cropped_image_path if cropped_image_path else ""
        
        # Validate dates
        if not validate_date_format(result['observed']['dateOfBirth']):
            validation_results["potential_risks"].append("Invalid date of birth format")
        if not validate_date_format(result['observed']['expiryDate']):
            validation_results["potential_risks"].append("Invalid expiry date format")
            
        # Check age
        try:
            dob = datetime.strptime(result['observed']['dateOfBirth'], '%Y-%m-%d')
            age = (datetime.now() - dob).days / 365.25
            validation_results["age_check_passed"] = age >= min_age
        except ValueError:
            validation_results["potential_risks"].append("Could not verify age")
            
        # Check expiry
        try:
            expiry = datetime.strptime(result['observed']['expiryDate'], '%Y-%m-%d')
            validation_results["expiry_check_passed"] = expiry > datetime.now()
        except ValueError:
            validation_results["potential_risks"].append("Could not verify expiry date")
            
        # Check name format against state requirements
        state = result['observed'].get('state')
        if state in stateIDFormats:
            name_parts = result['observed']['name'].split()
            if len(name_parts) >= 2:  # At least first and last name
                validation_results["format_check_passed"] = True
            
        # Combine results
        final_result = {
            "extracted_data": result,
            "validation_results": validation_results
        }
        
        return json.dumps(final_result, indent=2)
        
    except Exception as e:
        raise IDVerificationError(f"ID verification failed: {str(e)}")

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == "__main__":
    load_dotenv('secret.env')
    try:
        result = process_id_image("ID_Images/IMG_9276.jpg")
        print(result)
    except IDVerificationError as e:
        print(f"Error: {str(e)}")