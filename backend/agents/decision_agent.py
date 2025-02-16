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
 - ID Data (NAME, ADDRESS, DOB)
 - Face similarity
 - OSINT data about the same fields (NAME, ADDRESS, DOB) which may be partial or incomplete

**We only have, and only care about, the following data fields**:
 - Name (Full Name)
 - Address
 - Date of Birth
 - Face image

You may request more data outside of these four fields, but you cannot guarantee it will be provided. Further, it is generally not necessary, as to confirm a valid match, we only need to match the four fields above.

**You may request more data** if the OSINT data is insufficient. But only request clarifications or additional checks on NAME, ADDRESS, or DATE OF BIRTH.

Return only valid JSON with the following fields:

{
  "REASONING": "A short text explaining your reasoning.",
  "ACTION": one of ["REQUEST_MORE_DATA", "FINAL_VALID", "FINAL_INVALID"],
  "REQUEST_QUERY": "If ACTION=REQUEST_MORE_DATA, put a short query or direction for the OSINT agent here. Otherwise empty.",
  "CONFIDENCE_LEVEL": "One of [high, medium, low]"
}

Criteria for validity:
- Face match is relatively high (≥0.7).
- ID data (Name, Address, DOB) is consistent with OSINT data. 
- No strong red flags (e.g., different name or a totally different DOB from OSINT).

If the data is definitely contradictory, declare FINAL_INVALID.
If you are confident the ID is real, declare FINAL_VALID.
If you need more data regarding the Name, Address, or DOB, set ACTION=REQUEST_MORE_DATA and fill in REQUEST_QUERY with the data you need from OSINT. Only request clarifications on Name, Address, or DOB. Do not request data about SSN, job, phone, or relatives.
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
        self.verification_state = {
            "name": {"verified": False, "confidence": None},
            "address": {"verified": False, "confidence": None},
            "dob": {"verified": False, "confidence": None},
            "face": {"verified": False, "confidence": None}
        }
        self.decision_history = []  # Store previous decisions and reasoning

    def update_verification_state(self, id_data, face_similarity, osint_data):
        """Updates the verification state based on current data"""
        # Update face verification
        self.verification_state["face"] = {
            "verified": face_similarity >= 0.7,
            "confidence": face_similarity
        }

        # Extract name from ID and OSINT
        id_name = id_data.get("name", "").lower()
        osint_name = osint_data.get("person_info", {}).get("full_name", "").lower()
        self.verification_state["name"] = {
            "verified": id_name == osint_name,
            "confidence": "high" if id_name == osint_name else "low"
        }

        # Extract and compare DOB
        id_dob = id_data.get("dateOfBirth")
        osint_dob = osint_data.get("person_info", {}).get("date_of_birth")
        # You might need to standardize date formats here
        self.verification_state["dob"] = {
            "verified": id_dob == osint_dob,
            "confidence": "high" if id_dob == osint_dob else "low"
        }

        # Compare addresses (might need more sophisticated comparison)
        id_address = f"{id_data.get('address-line-1', '')} {id_data.get('address-line-2', '')}".lower()
        osint_current_address = next(
            (addr for addr in osint_data.get("addresses", []) if addr.get("current")),
            {}
        )
        osint_address = f"{osint_current_address.get('address', '')} {osint_current_address.get('city', '')} {osint_current_address.get('state', '')} {osint_current_address.get('zip', '')}".lower()
        
        self.verification_state["address"] = {
            "verified": id_address in osint_address or osint_address in id_address,
            "confidence": "high" if id_address in osint_address or osint_address in id_address else "low"
        }

    def make_final_decision(
        self, 
        id_data: Dict[str, Any], 
        face_similarity: float, 
        osint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregates sub-agent results and returns a JSON with decision:
          - REASONING
          - ACTION: "REQUEST_MORE_DATA" | "FINAL_VALID" | "FINAL_INVALID"
          - REQUEST_QUERY (if more data needed)
          - CONFIDENCE_LEVEL
        """
        self.update_verification_state(id_data, face_similarity, osint_data)

        # Format decision history for the prompt
        decision_history_text = "\n".join([
            f"Iteration {i+1}:"
            f"\nAction: {decision['ACTION']}"
            f"\nReasoning: {decision['REASONING']}"
            f"\nQuery: {decision['REQUEST_QUERY']}"
            f"\nConfidence: {decision['CONFIDENCE_LEVEL']}\n"
            for i, decision in enumerate(self.decision_history)
        ])

        content = f"""
        ID Data: {id_data}
        Face Similarity: {face_similarity}
        OSINT Data: {osint_data}
        Current Verification State: {json.dumps(self.verification_state, indent=2)}

        Previous Decisions:
        {decision_history_text if self.decision_history else "No previous decisions."}

        Now follow the instructions:
        {system_prompt}
        """

        chat_completion = create_chat_completion(content, llama_model, self.client)
        response_text = chat_completion.choices[0].message.content.strip()
        print("Raw DecisionAgent response:\n", response_text)

        # Clean and parse the response
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
        try:
            decision_output = json.loads(cleaned_response)
            # Store this decision in history
            self.decision_history.append(decision_output)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            decision_output = {
                "REASONING": "Could not parse LLM output; defaulting to invalid or uncertain.",
                "ACTION": "FINAL_INVALID",
                "REQUEST_QUERY": "",
                "CONFIDENCE_LEVEL": "low",
            }
            self.decision_history.append(decision_output)

        return decision_output

    def reset(self):
        """Reset the agent's state for a new verification"""
        self.verification_state = {
            "name": {"verified": False, "confidence": None},
            "address": {"verified": False, "confidence": None},
            "dob": {"verified": False, "confidence": None},
            "face": {"verified": False, "confidence": None}
        }
        self.decision_history = []

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
        