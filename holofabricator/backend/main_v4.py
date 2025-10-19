"""
HoloFabricator Backend v4 - 3D File Upload Support
- Upload 2D images OR 3D files (.glb, .obj, .ply)
- Direct Quest 3 scan support
- Better depth estimation (optional)
- All v3 features included
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, WebSocket, WebSocketDisconnect
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
import shutil

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import database
from database import (
    init_db, save_scan, get_scan, update_mesh_status,
    get_all_scans, save_chat
)

# Import Gemini Live services
try:
    from services.gemini_live import GeminiLiveClient, GeminiWebClient
    GEMINI_LIVE_AVAILABLE = True
except ImportError:
    print("[WARNING] Gemini Live services not available")
    GEMINI_LIVE_AVAILABLE = False

app = FastAPI(
    title="HoloFabricator API v4",
    description="Upload 2D images OR 3D scans from Quest 3",
    version="4.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path("uploads")
STATIC_DIR = Path("static")
MESH_DIR = Path("static/meshes")
WEBXR_DIR = Path("../webxr-app")
for dir in [UPLOAD_DIR, STATIC_DIR, MESH_DIR]:
    dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/app", StaticFiles(directory=str(WEBXR_DIR), html=True), name="webxr")

executor = ThreadPoolExecutor(max_workers=3)

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-pro')
    print("[OK] Gemini 2.5 Pro configured")
else:
    print("[WARNING] GEMINI_API_KEY not set")
    model = None

# Supported 3D formats
SUPPORTED_3D_FORMATS = {'.glb', '.obj', '.ply', '.stl', '.fbx'}
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}

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
    upload_type: str = "image"  # "image" or "3d_file"

class ChatRequest(BaseModel):
    scan_id: str
    question: str

class MeshData(BaseModel):
    vertices: List[List[float]]  # [[x,y,z], [x,y,z], ...]
    indices: List[int]  # Triangle indices
    semantic_label: Optional[str] = None  # "table", "chair", "global mesh", etc.

@app.on_event("startup")
async def startup_event():
    init_db()
    scans = get_all_scans()
    print(f"[OK] Database ready - {len(scans)} existing scans")

@app.get("/")
async def root():
    scans = get_all_scans()
    return {
        "name": "HoloFabricator API v4",
        "version": "4.0.0",
        "status": "operational" if GEMINI_API_KEY else "[WARNING] API key missing",
        "model": "Gemini 2.5 Pro",
        "features": {
            "2d_image_upload": True,
            "3d_file_upload": True,
            "quest_3_scan_support": True,
            "supported_3d_formats": list(SUPPORTED_3D_FORMATS),
            "async_processing": True,
            "persistent_storage": True
        },
        "total_scans": len(scans),
        "endpoints": {
            "POST /upload": "Upload 2D image OR 3D file",
            "POST /upload-webxr-mesh": "Upload WebXR detected mesh from Quest",
            "GET /analyze/{scan_id}": "Get results + mesh status",
            "POST /chat": "Ask questions about scanned object",
            "POST /search": "Search web with Gemini 2.5 Pro + Google Search",
            "WS /ws/voice": "Real-time voice conversation (Gemini Live API)",
            "GET /scans": "List all scans"
        },
        "gemini_features": {
            "vision_analysis": "gemini-2.5-pro",
            "voice_conversation": "gemini-live-2.5-flash-preview" if GEMINI_LIVE_AVAILABLE else "not available",
            "web_grounding": "Google Search integration",
            "native_audio": True if GEMINI_LIVE_AVAILABLE else False
        }
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Universal upload endpoint
    Accepts: 2D images (.jpg, .png) OR 3D files (.glb, .obj, .ply)
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    try:
        # Get file extension
        file_ext = Path(file.filename).suffix.lower()
        contents = await file.read()

        scan_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # Check if it's a 3D file
        if file_ext in SUPPORTED_3D_FORMATS:
            return await handle_3d_upload(scan_id, file_ext, contents, file.filename)

        # Otherwise treat as image
        elif file_ext in SUPPORTED_IMAGE_FORMATS:
            return await handle_image_upload(scan_id, contents)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Use: {SUPPORTED_IMAGE_FORMATS | SUPPORTED_3D_FORMATS}"
            )

    except Exception as e:
        print(f"[ERROR] Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_3d_upload(scan_id: str, file_ext: str, contents: bytes, filename: str):
    """
    Handle direct 3D file upload (Quest 3 scans, etc.)
    Skip mesh generation - use uploaded file directly!
    """
    print(f"\n[3D] 3D file upload: {scan_id}")

    # Save 3D file
    mesh_filename = f"{scan_id}_mesh{file_ext}"
    mesh_path = MESH_DIR / mesh_filename

    with open(mesh_path, 'wb') as f:
        f.write(contents)

    print(f"[OK] 3D file saved: {mesh_filename}")

    # Load mesh to get basic info
    try:
        if file_ext == '.ply':
            mesh = o3d.io.read_triangle_mesh(str(mesh_path))
        elif file_ext == '.obj':
            mesh = o3d.io.read_triangle_mesh(str(mesh_path))
        else:
            # For .glb, .stl - Open3D might not support, that's ok
            mesh = None

        # Get mesh statistics
        if mesh and mesh.has_vertices():
            vertices = np.asarray(mesh.vertices)
            bbox = mesh.get_axis_aligned_bounding_box()
            dimensions = bbox.get_extent()

            mesh_info = {
                "vertices": len(vertices),
                "dimensions": {
                    "width": f"{dimensions[0]:.2f}",
                    "height": f"{dimensions[1]:.2f}",
                    "depth": f"{dimensions[2]:.2f}"
                }
            }
        else:
            mesh_info = {"vertices": "unknown"}

    except Exception as e:
        print(f"[WARNING] Could not analyze mesh: {e}")
        mesh_info = {}

    # Try to render mesh to image for Gemini analysis
    image_path = await render_mesh_to_image(mesh_path, scan_id)

    if image_path:
        # Analyze rendered image with Gemini
        image = Image.open(image_path)
        analysis = await analyze_with_gemini(image, is_3d_scan=True)
    else:
        # Fallback: generic analysis
        analysis = {
            "object_name": f"3D Scan ({file_ext})",
            "category": "3D Model",
            "description": f"Uploaded 3D file: {filename}",
            "parts": [],
            "materials": ["Unknown"],
            "dimensions": mesh_info.get("dimensions", {}),
            "confidence": 0.5
        }

    analysis["upload_type"] = "3d_file"

    # Save to database with mesh already ready!
    save_scan(
        scan_id=scan_id,
        timestamp=datetime.now().isoformat(),
        image_path=str(image_path) if image_path else "",
        analysis=analysis,
        mesh_file=f"meshes/{mesh_filename}",
        mesh_status="ready"  # Already have the mesh!
    )

    print(f"[OK] 3D scan processed: {scan_id}")

    return {
        "scan_id": scan_id,
        "status": "success",
        "upload_type": "3d_file",
        "message": "3D file uploaded successfully!",
        "mesh_file": f"/static/meshes/{mesh_filename}",
        "mesh_status": "ready",
        "analysis": {
            **analysis,
            "mesh_status": "ready",
            "mesh_file": f"/static/meshes/{mesh_filename}"
        }
    }

async def handle_image_upload(scan_id: str, contents: bytes):
    """Handle 2D image upload (original v3 behavior)"""
    image = Image.open(io.BytesIO(contents))
    image_path = UPLOAD_DIR / f"{scan_id}.jpg"
    image.save(image_path, "JPEG")

    print(f"\n[IMAGE] Image upload: {scan_id}")

    # Analyze with Gemini
    analysis = await analyze_with_gemini(image, is_3d_scan=False)
    analysis["upload_type"] = "image"

    # Save to DB
    save_scan(
        scan_id=scan_id,
        timestamp=datetime.now().isoformat(),
        image_path=str(image_path),
        analysis=analysis,
        mesh_status="processing"
    )

    # Start async mesh generation
    print(f"[MESH] Generating 3D mesh (async)...")
    asyncio.create_task(generate_mesh_async(image, scan_id))

    return {
        "scan_id": scan_id,
        "status": "success",
        "upload_type": "image",
        "message": "Analysis complete. 3D mesh generating...",
        "analysis": {
            **analysis,
            "mesh_status": "processing"
        }
    }

async def analyze_with_gemini(image: Image.Image, is_3d_scan: bool = False):
    """Analyze image with Gemini 2.5 Pro"""
    print(f"[AI] Analyzing with Gemini 2.5 Pro...")

    context = "3D scanned model" if is_3d_scan else "photographed object"

    prompt = f"""
    Analyze this {context} as an expert engineer.

    Return ONLY valid JSON (no markdown):
    {{
        "object_name": "Specific name",
        "category": "Category",
        "description": "Detailed description (2-3 sentences)",
        "parts": [
            {{
                "name": "Part name",
                "function": "What it does",
                "location": "Where located",
                "material": "Material"
            }}
        ],
        "materials": ["Primary materials"],
        "dimensions": {{
            "estimated_width": "value cm",
            "estimated_height": "value cm",
            "estimated_depth": "value cm"
        }},
        "confidence": 0.95
    }}
    """

    response = model.generate_content([prompt, image])
    text = response.text.strip()

    # Parse JSON
    if "```json" in text:
        json_str = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        json_str = text.split("```")[1].split("```")[0].strip()
    else:
        json_str = text

    analysis = json.loads(json_str)
    print(f"[OK] Analysis: {analysis['object_name']}")
    return analysis

async def render_mesh_to_image(mesh_path: Path, scan_id: str) -> Optional[Path]:
    """Render 3D mesh to image for Gemini analysis"""
    try:
        mesh = o3d.io.read_triangle_mesh(str(mesh_path))
        if not mesh.has_vertices():
            return None

        # Create visualizer (headless)
        vis = o3d.visualization.Visualizer()
        vis.create_window(visible=False, width=800, height=600)
        vis.add_geometry(mesh)
        vis.update_geometry(mesh)
        vis.poll_events()
        vis.update_renderer()

        # Capture image
        image_path = UPLOAD_DIR / f"{scan_id}_render.jpg"
        vis.capture_screen_image(str(image_path))
        vis.destroy_window()

        return image_path

    except Exception as e:
        print(f"[WARNING] Mesh render failed: {e}")
        return None

# === V3 ENDPOINTS (unchanged) ===

@app.get("/analyze/{scan_id}")
async def get_analysis(scan_id: str):
    scan_data = get_scan(scan_id)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")

    result = {
        "scan_id": scan_data['scan_id'],
        "timestamp": scan_data['timestamp'],
        "mesh_status": scan_data['mesh_status'],
        "analysis": scan_data['analysis']
    }

    if scan_data['mesh_file'] and scan_data['mesh_status'] == 'ready':
        result['mesh_file'] = f"/static/{scan_data['mesh_file']}"
        result['analysis']['mesh_file'] = f"/static/{scan_data['mesh_file']}"

    return result

@app.post("/chat")
async def chat_about_object(request: ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini not configured")

    scan_data = get_scan(request.scan_id)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")

    analysis = scan_data['analysis']
    image_path = scan_data['image_path']

    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=400, detail="No image for chat")

    image = Image.open(image_path)

    prompt = f"""
    Object: {analysis['object_name']}
    Analysis: {json.dumps(analysis, indent=2)}

    Question: {request.question}

    Return JSON:
    {{
        "answer": "Detailed answer",
        "highlighted_parts": ["part1", "part2"]
    }}
    """

    response = model.generate_content([prompt, image])
    text = response.text.strip()

    if "```json" in text:
        json_str = text.split("```json")[1].split("```")[0].strip()
    else:
        json_str = text

    chat_response = json.loads(json_str)
    save_chat(request.scan_id, request.question,
              chat_response['answer'], chat_response['highlighted_parts'])

    return chat_response

@app.get("/scans")
async def list_scans():
    scans = get_all_scans()
    return {"total": len(scans), "scans": scans}

@app.post("/upload-webxr-mesh")
async def upload_webxr_mesh(mesh_data: MeshData):
    """
    Accept WebXR mesh detection data directly from Quest 3
    Converts vertices + indices → PLY mesh → Gemini analysis
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    try:
        print(f"\n[WEBXR] WebXR mesh upload: {len(mesh_data.vertices)} vertices")
        print(f"   Label: {mesh_data.semantic_label}")

        scan_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # Convert to Open3D mesh
        vertices = np.array(mesh_data.vertices)
        indices = np.array(mesh_data.indices).reshape(-1, 3)

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(indices)
        mesh.compute_vertex_normals()

        # Save as PLY
        mesh_filename = f"{scan_id}_webxr_mesh.ply"
        mesh_path = MESH_DIR / mesh_filename
        o3d.io.write_triangle_mesh(str(mesh_path), mesh)

        print(f"[OK] WebXR mesh saved: {mesh_filename}")

        # Render to image for Gemini
        image_path = await render_mesh_to_image(mesh_path, scan_id)

        if image_path:
            image = Image.open(image_path)
            analysis = await analyze_with_gemini(image, is_3d_scan=True)
        else:
            # Fallback
            analysis = {
                "object_name": mesh_data.semantic_label or "Detected Object",
                "category": "Scanned Object",
                "description": f"WebXR detected mesh with {len(vertices)} vertices",
                "parts": [],
                "materials": ["Unknown"],
                "confidence": 0.6
            }

        analysis["upload_type"] = "webxr_mesh"
        analysis["semantic_label"] = mesh_data.semantic_label

        # Save to database
        save_scan(
            scan_id=scan_id,
            timestamp=datetime.now().isoformat(),
            image_path=str(image_path) if image_path else "",
            analysis=analysis,
            mesh_file=f"meshes/{mesh_filename}",
            mesh_status="ready"
        )

        print(f"[OK] WebXR mesh processed: {scan_id}")

        return {
            "scan_id": scan_id,
            "status": "success",
            "upload_type": "webxr_mesh",
            "message": "WebXR mesh uploaded successfully!",
            "mesh_file": f"/static/meshes/{mesh_filename}",
            "mesh_status": "ready",
            "analysis": {
                **analysis,
                "mesh_status": "ready",
                "mesh_file": f"/static/meshes/{mesh_filename}"
            }
        }

    except Exception as e:
        print(f"[ERROR] WebXR mesh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MESH GENERATION (v3 code) ===

async def generate_mesh_async(image: Image.Image, scan_id: str):
    loop = asyncio.get_event_loop()
    try:
        mesh_file = await loop.run_in_executor(executor, generate_3d_mesh, image, scan_id)
        if mesh_file:
            update_mesh_status(scan_id, f"meshes/{mesh_file}", "ready")
            print(f"[OK] Mesh ready: {scan_id}")
        else:
            update_mesh_status(scan_id, None, "failed")
    except Exception as e:
        print(f"[ERROR] Mesh error: {e}")
        update_mesh_status(scan_id, None, "failed")

def generate_3d_mesh(image: Image.Image, scan_id: str) -> Optional[str]:
    """Generate mesh from 2D image (basic depth estimation)"""
    try:
        img_array = np.array(image)
        height, width = img_array.shape[:2]

        # Simple depth from brightness
        gray = np.mean(img_array, axis=2) / 255.0
        depth = 0.1 * (1 - gray)

        points = []
        colors = []
        scale = 0.01

        for y in range(0, height, 4):
            for x in range(0, width, 4):
                z = depth[y, x]
                points.append([x * scale, -y * scale, z])
                colors.append(img_array[y, x] / 255.0)

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors))
        pcd.estimate_normals()

        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=8)
        vertices_to_remove = densities < np.quantile(densities, 0.1)
        mesh.remove_vertices_by_mask(vertices_to_remove)

        mesh_file = f"{scan_id}_mesh.ply"
        mesh_path = MESH_DIR / mesh_file
        o3d.io.write_triangle_mesh(str(mesh_path), mesh)

        return mesh_file

    except Exception as e:
        print(f"[WARNING] Mesh gen error: {e}")
        return None

# === GEMINI 2.5 ENHANCED FEATURES ===

class WebSearchRequest(BaseModel):
    question: str
    context: Optional[str] = None
    scan_id: Optional[str] = None

class WebFetchRequest(BaseModel):
    url: str
    question: str
    context: Optional[str] = None
    scan_id: Optional[str] = None

@app.post("/search")
async def web_search(request: WebSearchRequest):
    """
    Ask Gemini 2.5 Pro a technical question using its knowledge base
    No web fetch - for quick Q&A
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    if not GEMINI_LIVE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Gemini Web client not available")

    try:
        web_client = GeminiWebClient(GEMINI_API_KEY)

        # If scan_id provided, add object context
        context = request.context
        if request.scan_id:
            scan_data = get_scan(request.scan_id)
            if scan_data:
                analysis = scan_data['analysis']
                context = f"Object: {analysis.get('object_name', 'Unknown')}\n{analysis.get('description', '')}"

        result = web_client.search_and_answer(request.question, context)

        return {
            "question": request.question,
            "answer": result["answer"],
            "model": result["model"]
        }

    except Exception as e:
        print(f"[ERROR] Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/web/fetch")
async def web_fetch(request: WebFetchRequest):
    """
    Fetch any website (text + images) and analyze with Gemini 2.5 Pro
    Full multimodal web scraping
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    if not GEMINI_LIVE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Gemini Web client not available")

    try:
        web_client = GeminiWebClient(GEMINI_API_KEY)

        # If scan_id provided, add object context
        context = request.context
        if request.scan_id:
            scan_data = get_scan(request.scan_id)
            if scan_data:
                analysis = scan_data['analysis']
                context = f"Object: {analysis.get('object_name', 'Unknown')}\n{analysis.get('description', '')}"

        result = web_client.fetch_and_analyze(request.url, request.question, context)

        return {
            "url": result["url"],
            "question": request.question,
            "answer": result["answer"],
            "images_analyzed": result["images_analyzed"],
            "text_length": result["text_length"],
            "model": result["model"]
        }

    except Exception as e:
        print(f"[ERROR] Web fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/voice")
async def voice_conversation(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice conversations
    Uses Gemini Live API with native audio
    """
    if not GEMINI_API_KEY:
        await websocket.close(code=1008, reason="API key not configured")
        return

    if not GEMINI_LIVE_AVAILABLE:
        await websocket.close(code=1011, reason="Gemini Live not available")
        return

    await websocket.accept()
    print("[VOICE] Client connected")

    live_client = GeminiLiveClient(GEMINI_API_KEY)

    try:
        # System instruction for HoloFabricator context
        system_instruction = """
        You are an expert AI assistant helping users in a mixed reality workshop.
        Users can show you objects, and you help them:
        - Identify parts and components
        - Explain how things work
        - Provide repair guidance
        - Answer technical questions
        - Search for specifications and datasheets

        Be concise, clear, and helpful. Speak naturally as if having a conversation.
        """

        # Connect to Gemini Live API
        connected = await live_client.connect(system_instruction)
        if not connected:
            await websocket.send_json({"error": "Failed to connect to Gemini Live"})
            return

        # Define callbacks for Gemini responses
        async def on_audio(audio_bytes: bytes):
            """Send audio response back to client"""
            await websocket.send_bytes(audio_bytes)

        async def on_text(text: str):
            """Send text response back to client"""
            await websocket.send_json({"type": "text", "content": text})

        # Start receiving from Gemini in background
        receive_task = asyncio.create_task(
            live_client.receive_stream(on_audio=on_audio, on_text=on_text)
        )

        # Handle client messages
        while True:
            message = await websocket.receive()

            if "bytes" in message:
                # Client sent audio
                audio_data = message["bytes"]
                await live_client.send_audio(audio_data)

            elif "text" in message:
                # Client sent text
                data = json.loads(message["text"])

                if data.get("type") == "text":
                    await live_client.send_text(data["content"])

                elif data.get("type") == "end":
                    break

    except WebSocketDisconnect:
        print("[VOICE] Client disconnected")
    except Exception as e:
        print(f"[VOICE] Error: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        await live_client.close()
        receive_task.cancel()


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("HoloFabricator v4 - Quest 3 Ready + Gemini 2.5!")
    print("=" * 70)
    print("[OK] Upload 2D images OR 3D scans (.glb, .obj, .ply)")
    print("[OK] Direct Quest 3 scan support")
    print("[OK] Gemini 2.5 Pro with Google Search")
    if GEMINI_LIVE_AVAILABLE:
        print("[OK] Gemini Live API for voice conversations")
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
