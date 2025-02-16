from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import json
from groq import Groq
import time

# ---------------------------------------------------------
# 4. Decision (Cross-Checking) Agent (Stub)
# ---------------------------------------------------------

deepseek_model = "deepseek-r1-distill-llama-70b"
llama_model = "llama-3.3-70b-versatile"

system_prompt = """
Given your context, decide if the ID information aligns with the other information we have gathered enough to be confident that the ID is real, or if there are enough misalignments such that we can be confident the ID is fake.

Success Criteria:
- Face photos match with high confidence
- ID data matches OSINT records
- No significant discrepancies found
- No evidence of fraud or manipulation
- Multiple data points confirm identity

Red Flags:
- Face mismatch
- Address discrepancies
- Age/DOB inconsistencies
- Recent ID issuance with older person
- Conflicting public records
- Signs of document manipulation

Return your answer in json format with only the following three fields.
1. REASONING: reasoning for the decision you are making
2. CONFIDENCE_LEVEL: high confidence, medium confidence, low confidence
3. STATUS: valid or invalid

"""

def create_chat_completion(content, model, client):  # New function to create chat completion
    return client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        model=model,
    )

def extract_json(text):  # Find content between json and markers
    start_marker = "json"
    end_marker = "```"
    
    try:
        # Find the start of JSON content
        start_index = text.find(start_marker) + len(start_marker)
        
        # Find the end of JSON content
        end_index = text.find(end_marker, start_index)
        
        if start_index == -1 or end_index == -1:
            raise ValueError("JSON markers not found in text")
            
        # Extract the JSON string
        json_str = text[start_index:end_index].strip()
        
        # Parse the JSON string
        return json.loads(json_str)
        
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        return None

def run_groq(content, model, client):
    chat_completion = create_chat_completion(content, model, client)
    response_content = chat_completion.choices[0].message.content
    print(response_content)
    return extract_json(response_content)

class DecisionAgent:
    """
    Agent responsible for combining all extracted data and making a final verification decision.
    Could be powered by an LLM (like Llama, GPT, or other) or a rule-based engine.
    """
    def __init__(self):
        load_dotenv('.env')  # Load variables from .env

        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    def make_final_decision(
        self, 
        id_data: Dict[str, Any], 
        face_similarity: float, 
        osint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregates all sub-agent results and generates a final decision.

        Args:
            parsed_data (Dict[str, Any]): The structured data from the ID.
            face_similarity (float): The face similarity score from FaceVerificationAgent.
            osint_data (Dict[str, Any]): The OSINT findings.

        Returns:
            Dict[str, Any]: Final decision output, including a confidence score and reasoning.
                {
                    "verificationScore": 0.95,
                    "status": "LIKELY_VALID",
                    "reasoning": "Face match is 85%. OSINT data consistent."
                }
        """
        # Example logic:
        #  - If face_similarity < 0.7 => High suspicion
        #  - If OSINT confidence < 0.5 => Uncertain
        #  - Additional checks on dateOfBirth vs. OSINT age
        #  - If no contradictions => likely valid

        content = f"""
        ID Data: {id_data}
        Face Similarity: {face_similarity}
        OSINT Data: {osint_data}
        """
        content += system_prompt
        return run_groq(content, llama_model, self.client)
    

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
        