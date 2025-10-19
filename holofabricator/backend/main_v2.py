"""HoloFabricator Backend v2 - Modular FastAPI application.

Upload image ➜ Gemini analysis ➜ Mesh generation ➜ Interactive exploration.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from config import settings
from models import ChatRequest, ChatResponse, UploadResponse
from services.gemini import GeminiClient, GeminiNotConfigured
from services.persistence import get_repository
from services.reconstruction import generate_mesh_from_image

logger = logging.getLogger("holofabricator.backend")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(title="HoloFabricator API v2", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

repository = get_repository(settings.database_path)
gemini_client = GeminiClient(settings.gemini_api_key)


def _save_uploaded_image(scan_id: str, image: Image.Image) -> Path:
    """Persist uploaded image to disk."""
    image_path = settings.upload_dir / f"{scan_id}.jpg"
    image_path.parent.mkdir(exist_ok=True)
    image.save(image_path, format="JPEG")
    return image_path


def _schedule_mesh_generation(background_tasks: BackgroundTasks, scan_id: str, image_path: Path) -> None:
    """Kick off background mesh generation."""
    background_tasks.add_task(_generate_mesh_for_scan, scan_id, str(image_path))


def _generate_mesh_for_scan(scan_id: str, image_path: str) -> None:
    """Background task to create mesh and persist metadata."""
    logger.info("Starting mesh generation for %s", scan_id)
    mesh_filename = generate_mesh_from_image(Path(image_path), settings.static_dir, scan_id)
    if mesh_filename:
        repository.update_mesh(scan_id, f"/static/{mesh_filename}", "ready")
        logger.info("Mesh generation complete for %s", scan_id)
    else:
        repository.update_mesh(scan_id, None, "failed")
        logger.warning("Mesh generation failed for %s", scan_id)


@app.get("/")
async def root() -> Dict[str, object]:
    """Service metadata."""
    status = "operational" if gemini_client.configured else "warning: gemini api key missing"
    return {
        "name": "HoloFabricator API v2",
        "version": app.version,
        "status": status,
        "model": "Gemini 2.5 Pro" if gemini_client.configured else "unconfigured",
        "storage": f"sqlite://{settings.database_path.name}",
        "endpoints": {
            "upload": "/upload",
            "analyse": "/analyze/{scan_id}",
            "chat": "/chat",
            "scans": "/scans",
        },
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> UploadResponse:
    """Upload an object image for analysis."""
    if not gemini_client.configured:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Add GEMINI_API_KEY to your environment.",
        )

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image") from exc

    scan_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S%f")
    image_path = _save_uploaded_image(scan_id, pil_image)

    try:
        analysis = gemini_client.analyse_image(pil_image)
    except GeminiNotConfigured as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Gemini analysis failed for %s", scan_id)
        raise HTTPException(status_code=502, detail=f"Gemini analysis failed: {exc}") from exc

    analysis.mesh_file = None
    analysis.mesh_status = "pending"

    repository.save_scan(scan_id, image_path, analysis)
    _schedule_mesh_generation(background_tasks, scan_id, image_path)

    return UploadResponse(scan_id=scan_id, status="analysis_complete", analysis=analysis)


@app.get("/analyze/{scan_id}")
async def get_analysis(scan_id: str) -> Dict[str, object]:
    """Retrieve analysis results for a scan."""
    record = repository.get_scan(scan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "scan_id": record.scan_id,
        "timestamp": record.created_at.isoformat(),
        "image_path": record.image_path,
        "analysis": record.analysis.dict(),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_about_object(request: ChatRequest) -> ChatResponse:
    """Answer questions about a scanned object."""
    if not gemini_client.configured:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Add GEMINI_API_KEY to your environment.",
        )

    record = repository.get_scan(request.scan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scan not found")

    try:
        with Image.open(record.image_path) as image:
            chat_response = gemini_client.answer_question(
                analysis=record.analysis,
                image=image.convert("RGB"),
                question=request.question,
            )
    except Exception as exc:
        logger.exception("Chat request failed for %s", request.scan_id)
        raise HTTPException(status_code=502, detail=f"Chat failed: {exc}") from exc

    return chat_response


@app.get("/scans")
async def list_scans() -> Dict[str, object]:
    """List all stored scans."""
    scans = repository.list_scans()
    return {
        "total": len(scans),
        "scans": scans,
    }


@app.on_event("shutdown")
def shutdown_event() -> None:
    """Cleanup resources on shutdown."""
    repository.close()


if __name__ == "__main__":
    import uvicorn

    if not gemini_client.configured:
        logger.warning("Gemini API key not set! Set GEMINI_API_KEY before starting the server.")

    uvicorn.run(
        "main_v2:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
