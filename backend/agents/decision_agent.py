# decision_agent.py

from typing import Dict, Any
import os
from dotenv import load_dotenv
import json
from groq import Groq
import time

deepseek_model = "deepseek-r1-distill-llama-70b"
llama_model = "llama-3.3-70b-versatile"

# We'll redefine this prompt so the DecisionAgent can request more data explicitly:
system_prompt = """
You are deciding if the ID is valid or not, based on:
 - ID Data
 - Face similarity
 - OSINT data (which may be partial or incomplete)
 - Past queries or new queries.

**You may request more data** if the OSINT data is insufficient.

Return only valid JSON with the following fields:

{
  "REASONING": "A short text explaining your reasoning.",
  "ACTION": one of ["REQUEST_MORE_DATA", "FINAL_VALID", "FINAL_INVALID"],
  "REQUEST_QUERY": "If ACTION=REQUEST_MORE_DATA, put a short query or direction for the OSINT agent here. Otherwise empty.",
  "CONFIDENCE_LEVEL": "One of [high, medium, low]"
}

Criteria for validity:
- Face match is relatively high (≥0.7 or so).
- ID data matches the OSINT data (or no major contradictions).
- No strong red flags.

If the data is definitely contradictory, declare FINAL_INVALID.
If you are confident the ID is real, declare FINAL_VALID.
If you need more data, set ACTION=REQUEST_MORE_DATA and fill in REQUEST_QUERY with the data you need from OSINT.
"""

def create_chat_completion(content, model, client):
    return client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        model=model,
    )

class DecisionAgent:
    """
    Agent responsible for combining all extracted data and making a final verification decision.
    Potentially an LLM with instructions on how to respond if more data is needed.
    """
    def __init__(self):
        load_dotenv('secret.env')  # Load variables from .env
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def make_final_decision(
        self, 
        id_data: Dict[str, Any], 
        face_similarity: float, 
        osint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregates sub-agent results and returns a JSON with:
          - REASONING
          - ACTION: "REQUEST_MORE_DATA" | "FINAL_VALID" | "FINAL_INVALID"
          - REQUEST_QUERY (if more data needed)
          - CONFIDENCE_LEVEL
        """
        content = f"""
        ID Data: {id_data}
        Face Similarity: {face_similarity}
        OSINT Data: {osint_data}

        Now follow the instructions:
        {system_prompt}
        """

        chat_completion = create_chat_completion(content, llama_model, self.client)
        response_text = chat_completion.choices[0].message.content.strip()
        print("Raw DecisionAgent response:\n", response_text)

        # Clean the response text by removing markdown code block markers
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()

        # Attempt to parse the JSON
        try:
            decision_output = json.loads(cleaned_response)
            print("decision_output_parsed")
        except json.JSONDecodeError as e:
            # Fallback: if parsing fails, we can default to an uncertain answer
            print(f"JSON parsing error: {e}")
            decision_output = {
                "REASONING": "Could not parse LLM output; defaulting to invalid or uncertain.",
                "ACTION": "FINAL_INVALID",
                "REQUEST_QUERY": "",
                "CONFIDENCE_LEVEL": "low",
            }
            print("decision_output parse failed")
        return decision_output
    

if __name__ == "__main__":
    decision_agent = DecisionAgent()
    mock_id_data = {
        "name": "Sarah Jane Wilson",
        "address-line-1": "1234 Maple Street",
        "address-line-2": "San Francisco, CA 94110",
        "dateOfBirth": "1992-03-15",
        "expirationDate": "2025-06-30",
        "stateOfIssue": "CA",
        "issueDate": "2021-06-30",
        "gender": "F",
        "height": "5'-6\"",
        "eyeColor": "BRN",
    }
    face_similarity = 0.85
    mock_osint_data = {
        "person_info": {
            "full_name": "Sarah Jane Wilson",
            "age": "31",
            "date_of_birth": "03/15/1992",
            "gender": "Female",
            "aliases": ["Sarah J Wilson", "Sarah Wilson"]
        },
        "addresses": [
            {
                "current": True,
                "address": "1234 Maple Street",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94110",
                "timespan": "2019-present"
            },
            {
                "current": False,
                "address": "567 Oak Avenue",
                "city": "Berkeley",
                "state": "CA",
                "zip": "94703",
                "timespan": "2015-2019"
            }
        ],
        "phone_numbers": [
            {
                "number": "(415) 555-0123",
                "type": "Mobile",
                "carrier": "Verizon"
            }
        ],
        "relatives": [
            {
                "name": "Michael Wilson",
                "relationship": "Father",
                "age": "58"
            },
            {
                "name": "Jennifer Wilson",
                "relationship": "Mother",
                "age": "56"
            }
        ],
        "employment": [
            {
                "employer": "Tech Solutions Inc",
                "title": "Software Engineer",
                "timespan": "2018-present"
            }
        ],
        "education": [
            {
                "institution": "UC Berkeley",
                "degree": "BS Computer Science",
                "graduation_year": "2014"
            }
        ],
        "social_media": [
            {
                "platform": "LinkedIn",
                "profile_url": "linkedin.com/in/sarahjwilson",
                "last_active": "2023"
            }
        ],
        "public_records": {
            "property_records": [
                {
                    "address": "1234 Maple Street",
                    "purchase_date": "2019-05",
                    "purchase_price": "$950,000"
                }
            ],
            "vehicle_registrations": [
                {
                    "make": "Toyota",
                    "model": "RAV4",
                    "year": "2020",
                    "state": "CA"
                }
            ],
            "licenses": [
                {
                    "type": "Driver's License",
                    "state": "CA",
                    "status": "Active",
                    "expiration": "2025-06-30"
                }
            ]
        },
        "data_confidence_score": 0.92,
        "last_updated": "2024-03-15"
    }
    start_time = time.time()
    print(decision_agent.make_final_decision(mock_id_data, face_similarity, mock_osint_data))
    end_time = time.time()
    print(f"Time for decision: {end_time - start_time} seconds")
        