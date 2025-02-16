import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from groq import Groq
import datetime

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
If you need more data regarding the Name, Address, or DOB, set ACTION=REQUEST_MORE_DATA and fill in REQUEST_QUERY with the data you need from OSINT. Only request clarifications on Name, Address, or DOB. Do not request data about SSN, phone, or relatives.
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


def do_dobs_match(id_dob_str: str, osint_dob_str: str, osint_age_str: str = "") -> bool:
    """
    1) If OSINT has a DOB string, parse both and check exact match.
    2) If OSINT lacks DOB but has an age, compare approximate age.
    """
    if osint_dob_str:
        id_date = parse_dob(id_dob_str)
        osint_date = parse_dob(osint_dob_str)
        if id_date and osint_date:
            return id_date == osint_date
        return False

    # If no OSINT DOB string but there's an OSINT age
    if osint_age_str:
        try:
            osint_age = int(osint_age_str)
        except:
            osint_age = None
        if not osint_age:
            return False

        id_date = parse_dob(id_dob_str)
        if not id_date:
            return False

        # Compare approximate age
        current_year = datetime.date.today().year
        possible_age = current_year - id_date.year
        # If we're within a year or two, call it good
        return abs(possible_age - osint_age) <= 2

    # If there's absolutely no OSINT DOB or age
    return False


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

        # 1) Face verification
        self.verification_state["face"] = {
            "verified": face_similarity >= 0.7,
            "confidence": face_similarity
        }

        # 2) Compare Name
        id_name = id_data.get("name", "").strip().lower()
        osint_name = osint_data.get("person_info", {}).get("full_name", "").strip().lower()
        name_verified = (id_name == osint_name) if (id_name and osint_name) else False

        self.verification_state["name"] = {
            "verified": name_verified,
            "confidence": "high" if name_verified else "low"
        }

        # 3) Compare DOB
        id_dob_str = id_data.get("dateOfBirth", "")
        # OSINT might have date_of_birth or might just have 'age'
        osint_dob_str = osint_data.get("person_info", {}).get("date_of_birth", "")
        osint_age_str = osint_data.get("person_info", {}).get("age", "")

        dob_verified = do_dobs_match(id_dob_str, osint_dob_str, osint_age_str)
        self.verification_state["dob"] = {
            "verified": dob_verified,
            "confidence": "high" if dob_verified else "low"
        }

        # 4) Compare address
        # Build the ID's full address
        id_address = (
            (id_data.get("address-line-1","") + " " + id_data.get("address-line-2",""))
            .strip()
            .lower()
        )

        # OSINT might have multiple addresses
        addresses = osint_data.get("addresses", [])
        address_verified = False
        for addr in addresses:
            full_osint_addr = (
                addr.get("address","") + " " +
                addr.get("city","") + " " +
                addr.get("state","") + " " +
                addr.get("zip","")
            ).strip().lower()
            # Simple substring check
            if id_address and full_osint_addr and (
                id_address in full_osint_addr or full_osint_addr in id_address
            ):
                address_verified = True
                break

        self.verification_state["address"] = {
            "verified": address_verified,
            "confidence": "high" if address_verified else "low"
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

        # Do a quick check for multiple mismatches or a direct contradiction
        mismatches = []
        for field in ["name","dob","address","face"]:
            if not self.verification_state[field]["verified"]:
                mismatches.append(field)

        # If we have multiple mismatches, let's short-circuit
        if len(mismatches) > 1:
            # Direct contradiction: we can finalize invalid
            return {
                "REASONING": f"Multiple mismatches: {mismatches}. The data is contradictory.",
                "ACTION": "FINAL_INVALID",
                "REQUEST_QUERY": "",
                "CONFIDENCE_LEVEL": "low"
            }

        # If everything is verified
        all_verified = all(self.verification_state[f]["verified"] for f in ["name","dob","address","face"])
        if all_verified:
            return {
                "REASONING": "All data matches across ID, face, and OSINT. Confident valid.",
                "ACTION": "FINAL_VALID",
                "REQUEST_QUERY": "",
                "CONFIDENCE_LEVEL": "high"
            }

        # If exactly one mismatch, the LLM prompt might want to do one more pass
        # But let's see if we want to yield to the LLM or do a direct approach
        # We'll continue letting the LLM attempt to form a final answer, but we supply the context
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
        cleaned_response = (
            response_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
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