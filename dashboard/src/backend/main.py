from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .similarity import compare_faces

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FaceCompareRequest(BaseModel):
    known_image: str
    unknown_image: str

@app.post("/compare-faces")
async def compare_face_images(request: FaceCompareRequest):
    try:
        result = compare_faces(request.known_image, request.unknown_image)
        return {"success": True, "result": bool(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 