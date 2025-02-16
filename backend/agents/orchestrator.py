import asyncio
from typing import Any, Dict, Optional
from enum import Enum
import os
import shutil

from agents.document_agent import DocumentParsingAgent
from agents.reverse_image_agent import ReverseImageAgent
from agents.face_verification_agent import FaceVerificationAgent
from agents.osint_agent import OSINTAgent
from agents.decision_agent import DecisionAgent
import json

class OrchestratorStatus(Enum):
    DORMANT = "DORMANT"
    AWAITING_LICENSE = "AWAITING_LICENSE"
    PROCESSING = "PROCESSING"

# Utility function to split names
def split_name(full_name):
    parts = full_name.strip().split()
    
    if len(parts) == 1:  # Only first name
        return parts[0], "", ""
    elif len(parts) == 2:  # First and last name
        return parts[0], "", parts[1]
    else:  # First, middle, last name (or more)
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
        
        # We'll store the results here
        self.reverse_image_agent_output = None
        self.face_similarity = None
        self.fast_people_results = None

    async def _cache_reverse_image_result(self):
        """Background task to cache the reverse image result when ready"""
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
                # Create the future but don't await it
                self.reverse_image_future = asyncio.create_task(
                    asyncio.to_thread(self.reverse_image_agent.run, image_url)
                )
                
                # Create a background task to cache the result when it's ready
                asyncio.create_task(self._cache_reverse_image_result())

            
        elif self.status == OrchestratorStatus.AWAITING_LICENSE:
            # License image
            self.status = OrchestratorStatus.PROCESSING
            self.license_image_url = image_url
            # Now run the main verification pipeline
            await self.run_verification()
            
        else:
            # Orchestrator is in PROCESSING or not ready to accept images
            pass

    def reset(self):
        print("Resetting orchestrator")
        # cancel any running tasks
        if self.reverse_image_agent_output:
            self.reverse_image_agent_output.cancel()
        if self.face_similarity:
            self.face_similarity.cancel()
        if self.fast_people_results:
            self.fast_people_results.cancel()
        self.status = OrchestratorStatus.DORMANT
        self.face_image_url = None
        self.license_image_url = None
        self.reverse_image_agent_output = None
        self.face_similarity = None
        self.fast_people_results = None
    
    async def run_verification(self) -> Dict[str, Any]:
        """
        Runs the entire identity verification pipeline asynchronously.
        """
        # 1. Parse the ID
        #    We'll run `parse_id_document` in a thread if it's blocking:
        print("urls: ", self.license_image_url, self.face_image_url)
        parsed_data = await asyncio.to_thread(
            self.document_parser.parse_id_document, self.license_image_url, self.face_image_url
        )
        
        if isinstance(parsed_data, str):
            parsed_data = json.loads(parsed_data)  # Convert JSON string to dictionary if needed
        observed_data = parsed_data["observed"]
        name = observed_data["name"]
        address1 = observed_data["address-line-1"]
        address2 = observed_data["address-line-2"]
        dateOfBirth = observed_data["dateOfBirth"]
        cropped_ID_image_path = observed_data["profileImage"]
        cropped_face_image_path = observed_data["faceImage"]

        print("cropped_ID_image_path ", cropped_ID_image_path)
        firstName, middleName, lastName = split_name(name)
        
        # 2. Face Verification
        #    This might be CPU-bound or GPU-bound, so run it in a thread:
        face_verification_future = asyncio.to_thread(
            self.face_verifier.compare_faces, cropped_ID_image_path, cropped_face_image_path
        )
        
        #copy both images to dashboard/public. Ensure that they use their existing names, but excluding the dirs they are in rn
        shutil.copy(cropped_ID_image_path, f"dashboard/public/{cropped_ID_image_path.split('/')[-1]}")
        shutil.copy(cropped_face_image_path, f"dashboard/public/{cropped_face_image_path.split('/')[-1]}")
        print("copied images to dashboard/public: ", cropped_ID_image_path.split('/')[-1], cropped_face_image_path.split('/')[-1])

        # 3. OSINT Checks
        #    Possibly also run in a thread if it does synchronous network calls:
        fast_people_future = asyncio.to_thread(
            self.osint_agent.run_fastpeople,
            {
                "FirstName": firstName,
                "MiddleName": middleName,
                "LastName": lastName,
                "address2": address2,
            }
        )

        # Run both calls concurrently
        self.face_similarity, self.fast_people_results = await asyncio.gather(
            face_verification_future, 
            fast_people_future
        )

        # AGENT LOOP
        
        # # 4. Combine everything and make a final decision
        # final_decision = self.decision_agent.decide(
        #     parsed_data, 
        #     self.face_similarity, 
        #     self.fast_people_results
        # )

        
        # make sure that all async variables have been awaited
        await asyncio.gather(
            self.face_similarity,
            self.fast_people_results,
            self.reverse_image_agent_output,
        )
        
        final_result = {
            "parsed_data": parsed_data,
            "face_similarity": self.face_similarity,
            "osint_results": self.fast_people_results,
            "reverse_image_agent_output": self.reverse_image_agent_output,
        }
        
        # write these to a file
        with open("results.json", "w") as f:
            json.dump(final_result, f)

        # Reset and return
        self.reset()
        return final_result