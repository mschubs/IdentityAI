from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from similarity import compare_faces
import shutil
import os
from datetime import datetime

from agents.orchestrator import OrchestratorAgent
from agents.document_agent import DocumentParsingAgent
from agents.face_verification_agent import FaceVerificationAgent
from agents.osint_agent import OSINTAgent
from agents.decision_agent import DecisionAgent
from agents.orchestrator import OrchestratorStatus
from agents.reverse_image_agent import ReverseImageAgent
app = FastAPI()

# Add CORS middleware - allow all origins for now (not recommended for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify the origins you want to allow
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class FaceCompareRequest(BaseModel):
    known_image: str
    unknown_image: str

doc_parser = DocumentParsingAgent()
face_verifier = FaceVerificationAgent()
osint_agent = OSINTAgent()
decision_agent = DecisionAgent()
reverse_image_agent = ReverseImageAgent()
# Create the orchestrator
orchestrator = OrchestratorAgent(
    document_parser=doc_parser,
    face_verifier=face_verifier,
    osint_agent=osint_agent,
    decision_agent=decision_agent,
    reverse_image_agent=reverse_image_agent
)

@app.post("/compare-faces")
async def compare_face_images(request: FaceCompareRequest):
    try:
        result = compare_faces(request.known_image, request.unknown_image)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    # Validate that the uploaded file is an image
    if not file.content_type.startswith('image/'):
        return {"error": "File must be an image"}
    
    # Create unique filename using timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    new_filename = f"{timestamp}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, new_filename)
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    print("awaiting orchestrator")
    # Pass image to orchestrator (async call)
    await orchestrator.accept_image(file_path)
    print("orchestrator done")
    # Optionally, if the orchestrator just finished RUN_VERIFICATION,
    # you might want to return something about the results. For example:
    if orchestrator.status == OrchestratorStatus.PROCESSING:
        # We may have a "final_result" if run_verification is done.
        # But if you want to respond right away (non-blocking), you could do so.
        print(f"Orchestrator state: {orchestrator.status.value}")
        return {"status": "Verification started, results will come later"}
    else:
        print(f"Orchestrator state: {orchestrator.status.value}")
        return {"status": f"Orchestrator state: {orchestrator.status.value}"}
    
    # Pass image to id to text, and gets this out
    # "observed": {
    #     "profileImage": str,
    #     "name": str,
    #     "address": str,
    #     "dateOfBirth": str,
    #     "expiryDate": str,
    #     "nationality": str,
    #     "gender": str
    # }
    #
    # Also gets a picture of the face and id_face out
    #
    # take face pic and id_face pic and pass to similarty
    #
    # take the face and pass to the pimeyes/firecrawl pipeline
    # get result that includes the markdown of all the articles/webpages where a picture of their face is found
    # 
    
    # agent time!

@app.post("/reset")
async def reset():
    orchestrator.reset()
    return {"status": "Orchestrator reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)