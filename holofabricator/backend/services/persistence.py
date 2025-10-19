"""SQLite-backed persistence for scan metadata."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import AnalysisResponse, ScanRecord


class ScanRepository:
    """Thread-safe repository for storing scan metadata."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._initialise()

    def _initialise(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id TEXT PRIMARY KEY,
                    image_path TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    mesh_file TEXT,
                    mesh_status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                );
                """
            )

    def save_scan(self, scan_id: str, image_path: Path, analysis: AnalysisResponse) -> None:
        """Insert or update a scan record."""
        payload = analysis.dict()
        mesh_file = payload.get("mesh_file")
        mesh_status = payload.get("mesh_status", "pending")
        created_at = datetime.utcnow().isoformat()

        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO scans (scan_id, image_path, analysis_json, mesh_file, mesh_status, created_at)
                VALUES (:scan_id, :image_path, :analysis_json, :mesh_file, :mesh_status, :created_at)
                ON CONFLICT(scan_id) DO UPDATE SET
                    image_path=excluded.image_path,
                    analysis_json=excluded.analysis_json,
                    mesh_file=excluded.mesh_file,
                    mesh_status=excluded.mesh_status
                """,
                {
                    "scan_id": scan_id,
                    "image_path": str(image_path),
                    "analysis_json": json.dumps(payload),
                    "mesh_file": mesh_file,
                    "mesh_status": mesh_status,
                    "created_at": created_at,
                },
            )

    def update_mesh(self, scan_id: str, mesh_file: Optional[str], mesh_status: str) -> None:
        """Update mesh metadata for a scan."""
        with self._lock, self._conn:
            row = self._conn.execute(
                "SELECT analysis_json FROM scans WHERE scan_id = ?", (scan_id,)
            ).fetchone()
            if not row:
                return

            analysis_payload: Dict = json.loads(row["analysis_json"])
            analysis_payload["mesh_file"] = mesh_file
            analysis_payload["mesh_status"] = mesh_status

            self._conn.execute(
                """
                UPDATE scans
                SET analysis_json = :analysis_json,
                    mesh_file = :mesh_file,
                    mesh_status = :mesh_status
                WHERE scan_id = :scan_id
                """,
                {
                    "analysis_json": json.dumps(analysis_payload),
                    "mesh_file": mesh_file,
                    "mesh_status": mesh_status,
                    "scan_id": scan_id,
                },
            )

    def get_scan(self, scan_id: str) -> Optional[ScanRecord]:
        """Fetch a single scan record."""
        row = self._conn.execute(
            "SELECT scan_id, image_path, analysis_json, created_at FROM scans WHERE scan_id = ?",
            (scan_id,),
        ).fetchone()
        if not row:
            return None

        analysis_data = json.loads(row["analysis_json"])
        analysis = AnalysisResponse(**analysis_data)
        created_at = datetime.fromisoformat(row["created_at"])
        return ScanRecord(
            scan_id=row["scan_id"],
            image_path=row["image_path"],
            analysis=analysis,
            created_at=created_at,
        )

    def list_scans(self) -> List[Dict[str, str]]:
        """Return summary information for all scans."""
        rows = self._conn.execute(
            "SELECT scan_id, analysis_json, created_at FROM scans ORDER BY created_at DESC"
        ).fetchall()

        results: List[Dict[str, str]] = []
        for row in rows:
            analysis_data = json.loads(row["analysis_json"])
            results.append(
                {
                    "scan_id": row["scan_id"],
                    "object_name": analysis_data.get("object_name", "unknown"),
                    "created_at": row["created_at"],
                    "mesh_status": analysis_data.get("mesh_status", "pending"),
                }
            )
        return results

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self._conn.close()


repository: Optional[ScanRepository] = None


def get_repository(db_path: Path) -> ScanRepository:
    """Return a singleton repository instance."""
    global repository
    if repository is None:
        repository = ScanRepository(db_path)
    return repository
