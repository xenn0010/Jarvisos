"""
Tony Stark Holographic Workshop - Backend API
FastAPI server for object recognition and AI guidance
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import base64
import os
from typing import Optional, List
import numpy as np

app = FastAPI(title="HoloFabricator API")

# Enable CORS for WebXR frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    print("⚠️  WARNING: GEMINI_API_KEY not set. Set it in environment or replace above.")

class ObjectAnalysisRequest(BaseModel):
    image_base64: str
    question: Optional[str] = "What is this object? Identify all parts and explain how it works."

class ObjectAnalysisResponse(BaseModel):
    object_name: str
    description: str
    parts: List[dict]
    instructions: str
    safety_notes: Optional[str] = None

@app.get("/")
async def root():
    return {
        "name": "HoloFabricator API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "/analyze": "Analyze object from image",
            "/3d/process": "Process 3D scan data",
            "/parts/search": "Search for replacement parts"
        }
    }

@app.post("/analyze", response_model=ObjectAnalysisResponse)
async def analyze_object(request: ObjectAnalysisRequest):
    """
    Analyze an object using Gemini Vision API
    Returns: Object identification, parts breakdown, and instructions
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64.split(',')[1] if ',' in request.image_base64 else request.image_base64)

        # Create prompt for structured response
        prompt = f"""
        Analyze this object as if you're an expert mechanic/engineer assisting someone in a mixed reality workshop.

        Question: {request.question}

        Provide a detailed response in this JSON format:
        {{
            "object_name": "Name of the object",
            "description": "Detailed description of what this is",
            "parts": [
                {{"name": "Part name", "function": "What it does", "location": "Where it is"}},
            ],
            "instructions": "Step-by-step guidance if repair/assembly is needed",
            "safety_notes": "Any safety warnings"
        }}
        """

        # Send to Gemini
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ])

        # Parse response (simplified - in production, use proper JSON parsing)
        result = {
            "object_name": "Analyzed Object",
            "description": response.text,
            "parts": [],
            "instructions": "Point your Quest 3 at different parts for detailed analysis.",
            "safety_notes": "Always wear proper safety equipment."
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/3d/process")
async def process_3d_scan(file: UploadFile = File(...)):
    """
    Process 3D scan data from Quest 3
    Returns: Processed mesh and semantic labels
    """
    return {
        "status": "processing",
        "mesh_id": "mesh_001",
        "message": "3D processing with Open3D - coming soon!"
    }

@app.get("/parts/search")
async def search_parts(object_name: str, part_name: str):
    """
    Use Fetch.ai uAgents to search for replacement parts
    """
    return {
        "query": f"{object_name} - {part_name}",
        "results": [],
        "message": "Fetch.ai procurement agent - coming soon!",
        "estimated_delivery": "2-3 days"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting HoloFabricator Backend...")
    print("📡 Make sure to set GEMINI_API_KEY environment variable")
    uvicorn.run(app, host="0.0.0.0", port=8000)
