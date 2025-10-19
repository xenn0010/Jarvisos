"""Pydantic models shared across the backend."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Part(BaseModel):
    """Description of a segmented part."""

    id: int = Field(default_factory=int)
    name: str
    function: Optional[str] = None
    material: Optional[str] = None
    location: Optional[str] = None
    additional: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    """Structured analysis returned to clients."""

    object_name: str
    category: str
    description: str
    parts: List[Dict[str, Any]]
    materials: List[str]
    dimensions: Optional[Dict[str, Any]] = None
    mesh_file: Optional[str] = None
    confidence: float
    mesh_status: str = Field(default="pending")


class ScanRecord(BaseModel):
    """Internal representation stored in persistence layer."""

    scan_id: str
    image_path: str
    analysis: AnalysisResponse
    created_at: datetime


class UploadResponse(BaseModel):
    """Response payload for upload endpoint."""

    scan_id: str
    status: str = "processing"
    analysis: AnalysisResponse


class ChatRequest(BaseModel):
    """Chat prompt payload."""

    scan_id: str
    question: str


class ChatResponse(BaseModel):
    """Chat response payload."""

    answer: str
    highlighted_parts: List[str] = Field(default_factory=list)
