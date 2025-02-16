import asyncio
from typing import Any, Dict, Optional
from enum import Enum

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

    async def accept_image(self, image_url: str):
        """
        Accepts an image and decides whether it's the face or the license,
        then triggers the appropriate sub-tasks.
        """
        if self.status == OrchestratorStatus.DORMANT:
            # Face image
            self.status = OrchestratorStatus.AWAITING_LICENSE
            self.face_image_url = image_url
            # Launch the reverse-image agent concurrently 
            # (since we want its result, but we don't have to block on it immediately).
            print("running reverse image agent")
            self.reverse_image_agent_output = self.reverse_image_agent.run(image_url)
            
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
        parsed_data = await asyncio.to_thread(
            self.document_parser.parse_id_document, self.license_image_url
        )
        
        name = parsed_data["name"]
        address1 = parsed_data["address-line-1"]
        address2 = parsed_data["address-line-2"]
        dateOfBirth = parsed_data["dateOfBirth"]
        id_face_image_path = parsed_data["capturedImage"]
        real_face_path = parsed_data["profileImage"]
        
        firstName, middleName, lastName = split_name(name)
        
        # 2. Face Verification
        #    This might be CPU-bound or GPU-bound, so run it in a thread:
        face_verification_future = asyncio.to_thread(
            self.face_verifier.compare_faces, id_face_image_path, real_face_path
        )
        
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

        # Return or store it
        self.reset()
        return