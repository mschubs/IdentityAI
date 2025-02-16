from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
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
    
    return {"filename": new_filename, "message": "Image uploaded successfully"}

@app.get("/images/{image_name}")
async def get_image(image_name: str):
    file_path = os.path.join(UPLOAD_DIR, image_name)
    if not os.path.exists(file_path):
        return {"error": "Image not found"}
    
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)