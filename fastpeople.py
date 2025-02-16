import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Get credentials from environment variables
key_name = os.getenv('ENDATO_KEY_NAME')
key_pass = os.getenv('ENDATO_KEY_PASS')

def search_person(payload):
    payload['FilterOptions'] = [
            "IncludeEmptyFirstNameResults",
            "IncludeSevenDigitPhoneNumbers",
            "IncludeLowQualityAddresses"
        ]

    url = "https://devapi.endato.com/PersonSearch"

    headers = {
        "accept": "application/json",
        "galaxy-ap-name": key_name,
        "galaxy-ap-password": key_pass,
        "galaxy-search-type": "Person",
        "content-type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.text

# Example usage
if __name__ == "__main__":
    sample_payload = {
        "FirstName": "Nandan",
        "MiddleName": "M",
        "LastName": "Srikrishna",
    }

    result = search_person(sample_payload)
    print(result)