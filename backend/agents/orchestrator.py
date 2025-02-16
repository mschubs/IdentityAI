from asyncore import loop
from document_agent import DocumentParsingAgent
from reverse_image_agent import ReverseImageAgent
from osint_agent import OSINTAgent 
from face_verification_agent import FaceVerificationAgent
from decision_agent import DecisionAgent
from typing import Any, Dict
import json
import asyncio
import concurrent.futures

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
        self.reverse_image_agent = reverse_image_agent

    def run_verification(
        self,
        uploaded_image: bytes
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
        parsed_data = self.document_parser.parse_id_document(uploaded_image)
        name = parsed_data["name"]
        address1 = parsed_data["address-line-1"]
        address2 = parsed_data["address-line-2"]
        dateOfBirth = parsed_data["dateOfBirth"]
        idFaceImage_path = parsed_data["capturedImage"]
        realFace_path = parsed_data["profileImage"]

        firstName, middleName, lastName = split_name(name)

        # 2. Face Verification
        face_similarity = self.face_verifier.compare_faces(idFaceImage_path, realFace_path)

        # Create a thread pool executor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Run the tasks concurrently
            website_data_task = executor.submit(
                self.reverse_image_agent.do_reverse_search, 
                realFace_path
            )
            osint_task = executor.submit(
                self.osint_agent.run_fastpeople,
                {
                    "FirstName": firstName,
                    "MiddleName": middleName,
                    "LastName": lastName,
                    "address2": address2,
                }
            )

            # Wait for both tasks to complete
            website_data = website_data_task.result()
            osint_data = osint_task.result()

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
    reverse_image_agent = ReverseImageAgent()
    # Create the orchestrator
    orchestrator = OrchestratorAgent(
        document_parser=doc_parser,
        reverse_image_agent=reverse_image_agent,
        face_verifier=face_verifier,
        osint_agent=osint_agent,
        decision_agent=decision_agent
    )    

    uploaded_image = "uploaded_image_path.jpg"

    # Run the pipeline
    verification_result = orchestrator.run_verification(
        uploaded_image=uploaded_image
    )

    # Print or log the output
    print(json.dumps(verification_result, indent=2))