from document_agent import DocumentParsingAgent
from reverse_image_agent import ReverseImageAgent
from osint_agent import OSINTAgent 
from face_verification_agent import FaceVerificationAgent
from decision_agent import DecisionAgent
from typing import Any, Dict
import json
from enum import Enum

# ---------------------------------------------------------
# 5. Orchestrator Agent
# ---------------------------------------------------------

def split_name(full_name):
    parts = full_name.strip().split()
    
    if len(parts) == 1:  # Only first name
        return parts[0], "", ""
    elif len(parts) == 2:  # First and last name
        return parts[0], "", parts[1]
    else:  # First, middle, last name (or more)
        return parts[0], " ".join(parts[1:-1]), parts[-1]
    
class OrchestratorStatus(Enum):
    DORMANT = "DORMANT"
    AWAITING_LICENSE = "AWAITING_LICENSE"
    PROCESSING = "PROCESSING"
    
class OrchestratorAgent:
    """
    The Orchestrator (Controller) Agent coordinates the entire verification pipeline.
    It spawns sub-agents to parse the ID, verify the face, gather OSINT data,
    and finally make a decision.
    """
    def __init__(
        self,
        document_parser: DocumentParsingAgent,
        reverse_image_agent: ReverseImageAgent,
        face_verifier: FaceVerificationAgent,
        osint_agent: OSINTAgent,
        decision_agent: DecisionAgent
    ):
        """
        Initializes the Orchestrator with its sub-agents.

        Args:
            document_parser (DocumentParsingAgent): Parses ID images.
            face_verifier (FaceVerificationAgent): Compares faces.
            osint_agent (OSINTAgent): Gathers OSINT data.
            decision_agent (DecisionAgent): Cross-checks and makes final decision.
        """
        self.document_parser = document_parser
        self.face_verifier = face_verifier
        self.osint_agent = osint_agent
        self.decision_agent = decision_agent
        self.status: OrchestratorStatus = OrchestratorStatus.DORMANT

    def accept_image(self, image_url: bytes):
        if self.status == OrchestratorStatus.DORMANT:
            # image is a face image
            # do the face image processing (reverse image agent)
            output = self.reverse_image_agent.run(image_url)
        elif self.status == OrchestratorStatus.AWAITING_LICENSE:
            # image is a license image
            # do the license image processing
            pass
        else:
            # do nothing, not in a state to accept images
            pass

    def run_verification(
        self,
        selfie_image: bytes,
        id_image: bytes
    ) -> Dict[str, Any]:
        """
        Runs the entire identity verification pipeline.

        Args:
            selfie_image (bytes): Binary data of the user's selfie/portrait.
            id_image (bytes): Binary data of the ID image.

        Returns:
            Dict[str, Any]: Final output containing parsed ID data, face similarity,
            OSINT findings, and final verification decision.
        """
        # 1. Parse the ID
        parsed_data = self.document_parser.parse_id_document(id_image)
        name = parsed_data["name"]
        address1 = parsed_data["address-line-1"]
        address2 = parsed_data["address-line-2"]
        dateOfBirth = parsed_data["dateOfBirth"]
        idFaceImage_path = parsed_data["capturedImage"]
        realFace_path = parsed_data["profileImage"]

        firstName, middleName, lastName = split_name(name)

        # 2. Face Verification
        face_similarity = self.face_verifier.compare_faces(idFaceImage_path, realFace_path)

        website_data_task = loop.run_in_executor(self.executor, self.reverse_image_agent.do_reverse_search, realFace_path)
        osint_task = loop.run_in_executor(self.executor, self.osint_agent.run_fastpeople, {
            "FirstName": firstName,
            "MiddleName": middleName,
            "LastName": lastName,
            "address2": address2,
        })

        # 3. Reverse Image Search
        website_data = self.reverse_image_agent.do_reverse_search(realFace_path)

        # 4. OSINT Checks (using either the ID face or the selfie)
        #    Typically you might pass the best quality face image available.
        fast_people_results = self.osint_agent.run_fastpeople({
            {
                "FirstName": firstName,
                "MiddleName": middleName,
                "LastName": lastName,
                "address2": address2,
            }
        })

        # 4. Final Decision
        decision_output = self.decision_agent.make_final_decision(
            parsed_data=parsed_data,
            face_similarity=face_similarity,
            osint_data=osint_data
        )

        # Combine everything into a final result object
        final_result = {
            "parsedData": parsed_data,
            "faceMatchScore": face_similarity,
            "osintData": osint_data,
            "decision": decision_output
        }
        return final_result

# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------
if __name__ == "__main__":
    # Instantiate sub-agents
    doc_parser = DocumentParsingAgent()
    face_verifier = FaceVerificationAgent()
    osint_agent = OSINTAgent()
    decision_agent = DecisionAgent()

    # Create the orchestrator
    orchestrator = OrchestratorAgent(
        document_parser=doc_parser,
        face_verifier=face_verifier,
        osint_agent=osint_agent,
        decision_agent=decision_agent
    )

    # Mock image data
    mock_selfie_data = b"mock_selfie_bytes"
    mock_id_data = b"mock_id_image_bytes"

    # Run the pipeline
    verification_result = orchestrator.run_verification(
        selfie_image=mock_selfie_data,
        id_image=mock_id_data
    )

    # Print or log the output
    print(json.dumps(verification_result, indent=2))