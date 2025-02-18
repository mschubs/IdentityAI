import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
import datetime

deepseek_model = "gpt-4o"
llama_model = "gpt-4o"

# Simplified prompt that doesn't allow requesting more data
system_prompt = """
You are deciding if the ID is valid or not, based on:
 - ID Data (NAME, ADDRESS, DOB)
 - Face similarity
 - OSINT data about the same fields (NAME, ADDRESS, DOB)

Return only valid JSON with the following fields:

{
  "REASONING": "A short text explaining your reasoning.",
  "ACTION": one of ["FINAL_VALID", "FINAL_INVALID"],
  "CONFIDENCE_LEVEL": "One of [high, medium, low]"
}

Criteria for validity:
- Face match is relatively high (≥0.7).
- ID data (Name, Address, DOB) is consistent with OSINT data. 
- No strong red flags (e.g., different name or a totally different DOB from OSINT).

If the data is definitely contradictory, declare FINAL_INVALID.
If you are confident the ID is real, declare FINAL_VALID.
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
        temperature=0,
    )


def parse_dob(dob_str: str):
    """
    Attempt to parse an incoming DOB string into a datetime.date object.
    Handles formats like YYYY-MM-DD, MM/DD/YYYY, etc.
    Return None if parsing fails.
    """
    dob_str = dob_str.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.datetime.strptime(dob_str, fmt).date()
        except ValueError:
            pass
    return None


def compare_dates_or_age(id_dob_str: str, osint_dob_str: str, osint_age_str: str = "") -> str:
    """
    Returns one of ["mismatch", "verified", "unknown"].

    1) If OSINT has a DOB string, parse both and check exact match => verified or mismatch.
    2) Else if OSINT only has an age, check approximate => verified or mismatch.
    3) If OSINT is missing DOB & age => unknown.
    """
    id_date = parse_dob(id_dob_str)

    # If we have an OSINT DOB string
    if osint_dob_str:
        osint_date = parse_dob(osint_dob_str)
        if id_date and osint_date:
            return "verified" if (id_date == osint_date) else "mismatch"
        else:
            # OSINT had a DOB, but we cannot parse it or the ID's. It's effectively mismatch or unknown.
            return "mismatch" if id_date else "unknown"

    # If we have no OSINT DOB string, but possibly have an age
    elif osint_age_str:
        try:
            osint_age = int(osint_age_str)
        except ValueError:
            osint_age = None
        
        if id_date and osint_age:
            current_year = datetime.date.today().year
            possible_age = current_year - id_date.year
            # If we're within ~2 years, call it "verified"
            if abs(possible_age - osint_age) <= 2:
                return "verified"
            else:
                return "mismatch"
        else:
            # We have an age, but can't parse ID DOB or the age is invalid => unknown or mismatch
            return "unknown" if not id_date else "mismatch"

    # If there's absolutely no OSINT DOB or age
    return "unknown"


class DecisionAgent:
    """
    Agent responsible for combining all extracted data and making a final verification decision.
    Potentially an LLM with instructions on how to respond if more data is needed.
    """
    def __init__(self):
        load_dotenv('secret.env')  # Load variables from .env
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Instead of booleans, store "status": in ["verified", "mismatch", "unknown"]
        self.verification_state = {
            "name": {"status": "unknown", "confidence": None},
            "address": {"status": "unknown", "confidence": None},
            "dob": {"status": "unknown", "confidence": None},
            "face": {"status": "unknown", "confidence": None}
        }

    def update_verification_state(self, id_data, face_similarity, osint_data):
        """Updates the verification state based on current data"""

        # Face verification: either verified or mismatch. 
        # If face_similarity is < 0.7, that is mismatch if we do have a face comparison.
        # If we have no face image at all, you could call it unknown, but presumably we do.
        if face_similarity >= 0.7:
            self.verification_state["face"] = {
                "status": "verified",
                "confidence": face_similarity
            }
        else:
            # If face_similarity is 0 => mismatch
            # if it's  -1 => maybe unknown if face wasn't recognized, etc. 
            # But let's keep it simple:
            self.verification_state["face"] = {
                "status": "mismatch",
                "confidence": face_similarity
            }

        # Compare Name
        id_name = id_data.get("name", "").strip().lower()
        osint_name = osint_data.get("person_info", {}).get("full_name", "").strip().lower()

        if not id_name:
            # If the ID didn't have a name for some reason, call it unknown
            self.verification_state["name"] = {"status": "unknown", "confidence": None}
        else:
            if not osint_name:
                # OSINT had no name => unknown
                self.verification_state["name"] = {"status": "unknown", "confidence": None}
            else:
                # We have both names
                if id_name == osint_name:
                    self.verification_state["name"] = {"status": "verified", "confidence": "high"}
                else:
                    self.verification_state["name"] = {"status": "mismatch", "confidence": "low"}

        # Compare DOB
        id_dob_str = id_data.get("dateOfBirth", "")
        osint_dob_str = osint_data.get("person_info", {}).get("date_of_birth", "")
        osint_age_str = osint_data.get("person_info", {}).get("age", "")

        dob_status = compare_dates_or_age(id_dob_str, osint_dob_str, osint_age_str)
        # You might want a confidence measure, e.g. "high" if verified, else "low"
        self.verification_state["dob"] = {
            "status": dob_status,
            "confidence": "high" if dob_status == "verified" else "low"
        }

        # Compare Address
        id_address = (
            (id_data.get("address-line-1","") + " " + id_data.get("address-line-2",""))
            .strip()
            .lower()
        )
        addresses = osint_data.get("addresses", [])

        if not id_address:
            self.verification_state["address"] = {"status": "unknown", "confidence": None}
        else:
            # We'll see if we find a match in OSINT
            found_match = False
            has_any_osint_address = False
            for addr in addresses:
                has_any_osint_address = True
                full_osint_addr = (
                    addr.get("address","") + " " +
                    addr.get("city","") + " " +
                    addr.get("state","") + " " +
                    addr.get("zip","")
                ).strip().lower()
                if full_osint_addr and (
                    id_address in full_osint_addr or full_osint_addr in id_address
                ):
                    found_match = True
                    break
            
            if not has_any_osint_address:
                # No addresses in OSINT => unknown
                self.verification_state["address"] = {"status": "unknown", "confidence": None}
            else:
                if found_match:
                    self.verification_state["address"] = {"status": "verified", "confidence": "high"}
                else:
                    self.verification_state["address"] = {"status": "mismatch", "confidence": "low"}

    def make_final_decision(
        self, 
        id_data: Dict[str, Any], 
        face_similarity: float, 
        osint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Return JSON with:
          - REASONING
          - ACTION: "FINAL_VALID" | "FINAL_INVALID"
          - CONFIDENCE_LEVEL
        """
        self.update_verification_state(id_data, face_similarity, osint_data)

        # Tally statuses
        statuses = {f: self.verification_state[f]["status"] for f in ["name","dob","address","face"]}
        mismatch_count = sum(1 for s in statuses.values() if s == "mismatch")
        verified_count = sum(1 for s in statuses.values() if s == "verified")
        unknown_count = sum(1 for s in statuses.values() if s == "unknown")

        # Make immediate decision if clear criteria are met
        if mismatch_count >= 1:
            return {
                "REASONING": f"Found {mismatch_count} mismatched fields: {statuses}",
                "ACTION": "FINAL_INVALID",
                "CONFIDENCE_LEVEL": "high" if mismatch_count >= 2 else "medium"
            }

        if verified_count == 4:
            return {
                "REASONING": "All fields verified successfully",
                "ACTION": "FINAL_VALID",
                "CONFIDENCE_LEVEL": "high"
            }

        # Check age consistency between ID and OSINT data
        id_age = id_data.get("calculatedAge")
        osint_age = None
        
        # Extract age from OSINT data using LLM
        age_prompt = f"""Given this OSINT data about a person, determine their age. 
        If multiple ages are found, return the most reliable one.
        If no exact age is found but you can infer it from other data, do so.
        Return only a number, or null if you cannot determine the age with reasonable confidence.

        OSINT Data: {json.dumps(osint_data, indent=2)}"""

        age_response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": age_prompt}],
            model="gpt-4o",
            temperature=0
        )
        
        osint_age = age_response.choices[0].message.content.strip()
        if osint_age.lower() == "null":
            osint_age = None
            
        if id_age and osint_age:
            try:
                id_age = int(id_age)
                osint_age = int(osint_age)
                
                # Allow for small discrepancies due to different reference dates
                if abs(id_age - osint_age) != 0:
                    return {
                        "REASONING": f"Age mismatch: ID shows {id_age}, OSINT shows {osint_age}",
                        "ACTION": "FINAL_INVALID",
                        "CONFIDENCE_LEVEL": "medium"
                    }
            except ValueError:
                # If age parsing fails, continue with other checks
                pass
        
        # For ambiguous cases, let the LLM make the final call
        content = f"""
        ID Data: {id_data}
        Face Similarity: {face_similarity}
        OSINT Data: {osint_data}
        Current Verification State: {json.dumps(self.verification_state, indent=2)}

        Make a final decision based on all available data.
        Fields verified: {verified_count}
        Fields unknown: {unknown_count}
        Fields mismatched: {mismatch_count}

        {system_prompt}
        """

        chat_completion = create_chat_completion(content, llama_model, self.client)
        response_text = chat_completion.choices[0].message.content.strip()
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            # Default to invalid if we can't parse the LLM response
            return {
                "REASONING": "Error parsing decision. Defaulting to invalid due to uncertainty.",
                "ACTION": "FINAL_INVALID",
                "CONFIDENCE_LEVEL": "low"
            }

    def reset(self):
        """Reset the agent's state for a new verification"""
        self.verification_state = {
            "name": {"status": "unknown", "confidence": None},
            "address": {"status": "unknown", "confidence": None},
            "dob": {"status": "unknown", "confidence": None},
            "face": {"status": "unknown", "confidence": None}
        }