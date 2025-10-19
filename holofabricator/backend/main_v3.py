"""
HoloFabricator Backend v3 - Production Ready
- SQLite database persistence (scans survive restarts)
- Async mesh generation (non-blocking)
- Mesh status polling (pending → processing → ready)
- Chat history tracking
- Gemini 2.5 Pro integration
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
from PIL import Image
import io
import os
import json
from pathlib import Path
from typing import Optional, List
import numpy as np
import open3d as o3d
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import database functions
from database import (
    init_db,
    save_scan,
    get_scan,
    update_mesh_status,
    get_all_scans,
    save_chat
)

app = FastAPI(
    title="HoloFabricator API v3",
    description="AI-powered object scanning with persistent storage",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("uploads")
STATIC_DIR = Path("static")
for dir in [UPLOAD_DIR, STATIC_DIR]:
    dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=3)

# Configure Gemini 2.5 Pro
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-pro')
    print("✅ Gemini 2.5 Pro configured")
else:
    print("⚠️  WARNING: GEMINI_API_KEY not set in .env file")
    model = None

# Models
class AnalysisResponse(BaseModel):
    object_name: str
    category: str
    description: str
    parts: List[dict]
    materials: List[str]
    dimensions: Optional[dict] = None
    mesh_file: Optional[str] = None
    mesh_status: str = "pending"
    confidence: float

class ChatRequest(BaseModel):
    scan_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    highlighted_parts: List[str]

# Startup: Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    existing_scans = get_all_scans()
    print(f"✅ Database ready - {len(existing_scans)} existing scans loaded")
    if existing_scans:
        print("📦 Scans will persist across restarts")

@app.get("/")
async def root():
    scans = get_all_scans()
    return {
        "name": "HoloFabricator API v3",
        "version": "3.0.0",
        "status": "operational" if GEMINI_API_KEY else "⚠️ API key missing",
        "model": "Gemini 2.5 Pro",
        "database": "SQLite (persistent)",
        "total_scans": len(scans),
        "features": {
            "async_mesh_generation": True,
            "persistent_storage": True,
            "chat_history": True,
            "mesh_status_polling": True
        },
        "endpoints": {
            "POST /upload": "Upload image for analysis",
            "GET /analyze/{scan_id}": "Get analysis + poll mesh status",
            "POST /chat": "Ask questions about object",
            "GET /scans": "List all scans",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini": "configured" if GEMINI_API_KEY else "missing_key",
        "database": "connected"
    }

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload image and analyze with Gemini 2.5 Pro
    Returns immediately with scan_id
    3D mesh generates asynchronously (poll /analyze/{scan_id} for status)
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Add GEMINI_API_KEY to .env file"
        )

    try:
        # Read and save uploaded image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Generate unique scan ID
        scan_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        image_path = UPLOAD_DIR / f"{scan_id}.jpg"
        image.save(image_path, "JPEG")

        print(f"\n📸 New upload: {scan_id}")
        print(f"🧠 Analyzing with Gemini 2.5 Pro...")

        # Analyze with Gemini
        prompt = """
        Analyze this object as an expert engineer. Provide detailed technical analysis.

        Return ONLY valid JSON (no markdown, no code blocks) with this structure:
        {
            "object_name": "Specific name of the object",
            "category": "Category (mechanical/electronic/tool/automotive/etc)",
            "description": "Detailed technical description (2-3 sentences)",
            "parts": [
                {
                    "name": "Part name",
                    "function": "What it does",
                    "location": "Where it's located",
                    "material": "What it's made of"
                }
            ],
            "materials": ["List of primary materials"],
            "dimensions": {
                "estimated_width": "value in cm",
                "estimated_height": "value in cm",
                "estimated_depth": "value in cm"
            },
            "confidence": 0.95
        }

        Be specific and identify as many parts as possible.
        """

        response = model.generate_content([prompt, image])
        analysis_text = response.text.strip()

        # Parse JSON (handle markdown code blocks)
        if "```json" in analysis_text:
            json_str = analysis_text.split("```json")[1].split("```")[0].strip()
        elif "```" in analysis_text:
            json_str = analysis_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = analysis_text

        analysis = json.loads(json_str)
        print(f"✅ Analysis complete: {analysis['object_name']}")

        # Save to database with "processing" status
        save_scan(
            scan_id=scan_id,
            timestamp=datetime.now().isoformat(),
            image_path=str(image_path),
            analysis=analysis,
            mesh_file=None,
            mesh_status="processing"
        )
        print(f"💾 Saved to database: {scan_id}")

        # Start async mesh generation
        print(f"🎨 Starting 3D mesh generation (async)...")
        asyncio.create_task(generate_mesh_async(image, scan_id))

        # Return immediately
        return {
            "scan_id": scan_id,
            "status": "success",
            "message": "Analysis complete. 3D mesh is generating. Poll /analyze/{scan_id} for mesh status.",
            "analysis": {
                **analysis,
                "mesh_status": "processing"
            }
        }

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw response: {analysis_text[:500]}...")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Gemini response. Response might not be valid JSON."
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analyze/{scan_id}")
async def get_analysis(scan_id: str):
    """
    Get analysis results and mesh status
    Poll this endpoint to check when mesh is ready

    mesh_status values:
    - "processing": Mesh is being generated
    - "ready": Mesh is available at mesh_file URL
    - "failed": Mesh generation failed
    """
    scan_data = get_scan(scan_id)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Build response
    result = {
        "scan_id": scan_data['scan_id'],
        "timestamp": scan_data['timestamp'],
        "mesh_status": scan_data['mesh_status'],
        "analysis": scan_data['analysis']
    }

    # Add full mesh URL if ready
    if scan_data['mesh_file'] and scan_data['mesh_status'] == 'ready':
        result['mesh_file'] = f"/static/{scan_data['mesh_file']}"
        result['analysis']['mesh_file'] = f"/static/{scan_data['mesh_file']}"

    return result

@app.post("/chat")
async def chat_about_object(request: ChatRequest):
    """
    Ask Gemini questions about a scanned object
    Returns answer and highlights relevant parts
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    scan_data = get_scan(request.scan_id)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")

    analysis = scan_data['analysis']

    try:
        # Load original image
        image_path = scan_data['image_path']
        image = Image.open(image_path)

        # Context-aware prompt
        prompt = f"""
        You are analyzing this object: {analysis['object_name']}

        Previous analysis:
        {json.dumps(analysis, indent=2)}

        User question: {request.question}

        Provide a detailed answer and list which parts are relevant.

        Return ONLY valid JSON (no markdown):
        {{
            "answer": "Detailed answer here",
            "highlighted_parts": ["part1", "part2"]
        }}
        """

        response = model.generate_content([prompt, image])
        response_text = response.text.strip()

        # Parse response
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text

        chat_response = json.loads(json_str)

        # Save to database
        save_chat(
            scan_id=request.scan_id,
            question=request.question,
            answer=chat_response['answer'],
            highlighted_parts=chat_response['highlighted_parts']
        )

        return chat_response

    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/scans")
async def list_scans():
    """List all scanned objects from database"""
    scans = get_all_scans()
    return {
        "total": len(scans),
        "scans": scans
    }

# === ASYNC MESH GENERATION ===

async def generate_mesh_async(image: Image.Image, scan_id: str):
    """
    Generate 3D mesh asynchronously in background
    Updates database when complete
    """
    loop = asyncio.get_event_loop()
    try:
        print(f"🔄 Generating mesh for {scan_id}...")
        mesh_file = await loop.run_in_executor(executor, generate_3d_mesh, image, scan_id)

        if mesh_file:
            update_mesh_status(scan_id, mesh_file, "ready")
            print(f"✅ Mesh ready: {scan_id} → {mesh_file}")
        else:
            update_mesh_status(scan_id, None, "failed")
            print(f"❌ Mesh generation failed: {scan_id}")

    except Exception as e:
        print(f"❌ Mesh error for {scan_id}: {e}")
        update_mesh_status(scan_id, None, "failed")

def generate_3d_mesh(image: Image.Image, scan_id: str) -> Optional[str]:
    """
    Generate 3D mesh from single image
    Uses depth estimation + Open3D reconstruction
    """
    try:
        # Convert to numpy
        img_array = np.array(image)
        height, width = img_array.shape[:2]

        # Simple depth map from brightness (placeholder for ML depth estimation)
        gray = np.mean(img_array, axis=2) / 255.0
        depth = 0.1 * (1 - gray)

        # Create point cloud
        points = []
        colors = []

        scale = 0.01
        for y in range(0, height, 4):  # Subsample
            for x in range(0, width, 4):
                z = depth[y, x]
                points.append([x * scale, -y * scale, z])  # Flip Y for proper orientation
                colors.append(img_array[y, x] / 255.0)

        # Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors))

        # Estimate normals
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )

        # Create mesh via Poisson reconstruction
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=8
        )

        # Remove low-density vertices
        vertices_to_remove = densities < np.quantile(densities, 0.1)
        mesh.remove_vertices_by_mask(vertices_to_remove)

        # Save mesh
        mesh_file = f"{scan_id}_mesh.ply"
        mesh_path = STATIC_DIR / mesh_file
        o3d.io.write_triangle_mesh(str(mesh_path), mesh)

        return mesh_file

    except Exception as e:
        print(f"⚠️ Mesh generation error: {e}")
        return None

# === MAIN ===

if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("🚀 HoloFabricator Backend v3 - Production Ready")
    print("=" * 70)

    if not GEMINI_API_KEY:
        print("\n⚠️  IMPORTANT: GEMINI_API_KEY not set!")
        print("   1. Get API key: https://makersuite.google.com/app/apikey")
        print("   2. Add to .env: GEMINI_API_KEY=your-key-here")
        print("   3. Restart server")
        print("\n⚠️  SECURITY: Never commit .env to git! Rotate key if shared.\n")
    else:
        print(f"✅ Gemini 2.5 Pro configured")

    print("\n📡 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("💾 Database: backend/holofabricator.db")
    print("🔄 Features: Async mesh, persistent storage, polling support")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
