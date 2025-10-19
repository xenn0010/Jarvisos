"""
Database layer for HoloFabricator
Persists scans across server restarts using SQLite
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = Path(__file__).parent / "holofabricator.db"

def init_db():
    """Initialize database schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            scan_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            image_path TEXT NOT NULL,
            analysis TEXT NOT NULL,
            mesh_file TEXT,
            mesh_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            highlighted_parts TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized: {DB_PATH}")

def save_scan(scan_id: str, timestamp: str, image_path: str, analysis: dict, mesh_file: Optional[str] = None, mesh_status: str = "pending"):
    """Save or update a scan"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO scans (scan_id, timestamp, image_path, analysis, mesh_file, mesh_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (scan_id, timestamp, image_path, json.dumps(analysis), mesh_file, mesh_status))

    conn.commit()
    conn.close()

def get_scan(scan_id: str) -> Optional[Dict]:
    """Retrieve a scan by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT scan_id, timestamp, image_path, analysis, mesh_file, mesh_status
        FROM scans WHERE scan_id = ?
    """, (scan_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "scan_id": row[0],
            "timestamp": row[1],
            "image_path": row[2],
            "analysis": json.loads(row[3]),
            "mesh_file": row[4],
            "mesh_status": row[5]
        }
    return None

def update_mesh_status(scan_id: str, mesh_file: str, status: str = "ready"):
    """Update mesh file and status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE scans SET mesh_file = ?, mesh_status = ?
        WHERE scan_id = ?
    """, (mesh_file, status, scan_id))

    conn.commit()
    conn.close()

def get_all_scans() -> List[Dict]:
    """Get all scans"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT scan_id, timestamp, analysis, mesh_status
        FROM scans ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    scans = []
    for row in rows:
        analysis = json.loads(row[2])
        scans.append({
            "scan_id": row[0],
            "timestamp": row[1],
            "object_name": analysis.get("object_name", "Unknown"),
            "mesh_status": row[3]
        })

    return scans

def save_chat(scan_id: str, question: str, answer: str, highlighted_parts: List[str]):
    """Save chat interaction"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_history (scan_id, question, answer, highlighted_parts)
        VALUES (?, ?, ?, ?)
    """, (scan_id, question, answer, json.dumps(highlighted_parts)))

    conn.commit()
    conn.close()
