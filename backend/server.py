from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.similarity import compare_faces
import shutil
import os
from datetime import datetime


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
    
    return {"filename": new_filename, "message": "Image uploaded successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)