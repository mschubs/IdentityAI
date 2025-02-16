import asyncio
from typing import Any, Dict, Optional
from enum import Enum
import os
import shutil
import json
import datetime

from document_agent import DocumentParsingAgent
from reverse_image_agent import ReverseImageAgent
from face_verification_agent import FaceVerificationAgent
from osint_agent import OSINTAgent
from decision_agent import DecisionAgent

class OrchestratorStatus(Enum):
    DORMANT = "DORMANT"
    AWAITING_LICENSE = "AWAITING_LICENSE"
    PROCESSING = "PROCESSING"

def split_name(full_name):
    parts = full_name.strip().split()
    if len(parts) == 1:  # Only first name
        return parts[0], "", ""
    elif len(parts) == 2:  # First and last name
        return parts[0], "", parts[1]
    else:  # e.g., First, Middle, Last
        return parts[0], " ".join(parts[1:-1]), parts[-1]

class OrchestratorAgent:
    def __init__(
        self,
        document_parser: DocumentParsingAgent,
        reverse_image_agent: ReverseImageAgent,
        face_verifier: FaceVerificationAgent,
        osint_agent: OSINTAgent,
        decision_agent: DecisionAgent,
    ):
        self.document_parser = document_parser
        self.reverse_image_agent = reverse_image_agent
        self.face_verifier = face_verifier
        self.osint_agent = osint_agent
        self.decision_agent = decision_agent

        self.status: OrchestratorStatus = OrchestratorStatus.DORMANT
        self.face_image_url: Optional[str] = None
        self.license_image_url: Optional[str] = None

        self.reverse_image_agent_output = None
        self.face_similarity = None
        self.fast_people_results = None

    async def _cache_reverse_image_result(self):
        """Background task to cache the reverse image result when ready."""
        result = await self.reverse_image_future
        self.reverse_image_agent_output = result
        with open("reverse_image_agent_output.json", "w") as f:
            json.dump(result, f)

    async def accept_image(self, image_url: str):
        """
        Accepts an image and decides whether it's the face or the license,
        then triggers the appropriate sub-tasks.
        """
        if self.status == OrchestratorStatus.DORMANT:
            self.status = OrchestratorStatus.AWAITING_LICENSE
            self.face_image_url = image_url
            print("running reverse image agent")

            # Load from cache if available
            if os.path.exists("reverse_image_agent_output.json"):
                with open("reverse_image_agent_output.json", "r") as f:
                    self.reverse_image_agent_output = json.load(f)
            else:
                self.reverse_image_future = asyncio.create_task(
                    asyncio.to_thread(self.reverse_image_agent.run, image_url)
                )
                asyncio.create_task(self._cache_reverse_image_result())

        elif self.status == OrchestratorStatus.AWAITING_LICENSE:
            # License image
            self.status = OrchestratorStatus.PROCESSING
            self.license_image_url = image_url
            await self.run_verification()  # The main pipeline
        else:
            # Orchestrator is in PROCESSING or not ready for images
            pass

    def reset(self):
        print("Resetting orchestrator")
        if hasattr(self, 'reverse_image_future'):
            if not self.reverse_image_future.done():
                self.reverse_image_future.cancel()
            delattr(self, 'reverse_image_future')

        self.status = OrchestratorStatus.DORMANT
        self.face_image_url = None
        self.license_image_url = None
        self.reverse_image_agent_output = None
        self.face_similarity = None
        self.fast_people_results = None

    async def run_verification(self) -> Dict[str, Any]:
        """
        Runs the entire identity verification pipeline asynchronously, using multiple OSINT tools
        in a single pass, then makes a final decision.
        """
        print("urls: ", self.license_image_url, self.face_image_url)
        
        # Step 1: Parse ID
        parsed_data = await asyncio.to_thread(
            self.document_parser.parse_id_document, self.license_image_url, self.face_image_url
        )
        if isinstance(parsed_data, str):
            parsed_data = json.loads(parsed_data)  # If it came back as JSON string

        observed_data = parsed_data["observed"]
        name = observed_data["name"]
        address1 = observed_data["address-line-1"]
        address2 = observed_data["address-line-2"]
        dateOfBirth = observed_data["dateOfBirth"]
        
        # Add age calculation via LLM
        age_prompt = f"""Given today's date and a date of birth, calculate the person's current age.
        Date of Birth: {dateOfBirth}
        Today's Date: {datetime.date.today()}
        
        Return only a number representing the age in years."""
        
        age_response = self.decision_agent.client.chat.completions.create(
            messages=[{"role": "user", "content": age_prompt}],
            model="gpt-4o",
            temperature=0
        )
        calculated_age = age_response.choices[0].message.content.strip()
        observed_data["calculatedAge"] = calculated_age

        print("birthday: ", dateOfBirth)
        print("calculated_age: ", calculated_age)
        
        cropped_ID_image_path = observed_data["profileImage"]
        cropped_face_image_path = observed_data["faceImage"]

        firstName, middleName, lastName = split_name(name)

        # Step 2: Face Verification
        face_verification_future = asyncio.to_thread(
            self.face_verifier.compare_faces, 
            cropped_ID_image_path, 
            cropped_face_image_path
        )

        # Copy the cropped images to a known location for the dashboard
        shutil.copy(cropped_ID_image_path, f"dashboard/public/{os.path.basename(cropped_ID_image_path)}")
        shutil.copy(cropped_face_image_path, f"dashboard/public/{os.path.basename(cropped_face_image_path)}")
        print("Copied images to dashboard/public:", cropped_ID_image_path, cropped_face_image_path)

        # Step 3: OSINT calls
        # Run FastPeople and Sonar queries in parallel
        fast_people_future = asyncio.to_thread(
            self.osint_agent.run_fastpeople,
            {
                "FirstName": firstName,
                "MiddleName": middleName,
                "LastName": lastName,
                "address2": address2,
            }
        )

        sonar_query = f"Verify name '{name}' and date of birth '{dateOfBirth}' using public records"
        sonar_future = asyncio.to_thread(
            self.osint_agent.run_sonar_query,
            sonar_query
        )

        # Gather all async results in parallel
        self.face_similarity, fast_people_result, sonar_result = await asyncio.gather(
            face_verification_future, 
            fast_people_future,
            sonar_future
        )

        # If we haven't collected reverse_image results yet, wait for it
        if hasattr(self, 'reverse_image_future') and not self.reverse_image_agent_output:
            await self.reverse_image_future

        # Consolidate OSINT data
        try:
            fast_people_json = json.loads(fast_people_result)
        except:
            fast_people_json = {"rawResponse": fast_people_result}

        osint_data = {
            "person_info": {  # Restructured to match decision agent's expected format
                "full_name": name,
                "date_of_birth": dateOfBirth,
                "age": fast_people_json.get("age", "")
            },
            "addresses": [
                {
                    "address": address1,
                    "city": "",  # These could be parsed from address2 if needed
                    "state": "",
                    "zip": address2
                }
            ],
            "fastPeople": fast_people_json,
            "sonar": sonar_result,
            "reverseImage": self.reverse_image_agent_output or {}
        }

        # Step 4: Make final decision with all available data
        final_result = self.decision_agent.make_final_decision(
            id_data=observed_data,
            face_similarity=self.face_similarity,
            osint_data=osint_data
        )

        # Step 5: Persist results
        with open("results.json", "w") as f:
            json.dump(final_result, f, indent=2)

        # Step 6: Reset everything to accept the next user
        self.reset()
        return final_result


# ------------------
# Example usage:
# ------------------
async def process_images():
    document_parser = DocumentParsingAgent()
    reverse_image_agent = ReverseImageAgent()
    face_verifier = FaceVerificationAgent()
    osint_agent = OSINTAgent()
    decision_agent = DecisionAgent()    
    orchestrator = OrchestratorAgent(
        document_parser, reverse_image_agent, face_verifier, osint_agent, decision_agent
    )
    await orchestrator.accept_image("/Users/derekmiller/Downloads/nandan_face.jpg")
    await orchestrator.accept_image("/Users/derekmiller/Downloads/nandan_id.jpg")


if __name__ == "__main__":
    asyncio.run(process_images())