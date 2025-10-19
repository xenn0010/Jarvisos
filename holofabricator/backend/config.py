"""Configuration helpers for the HoloFabricator backend."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        load_dotenv()
        self.root_dir: Path = Path(__file__).resolve().parent
        self.upload_dir: Path = self.root_dir / "uploads"
        self.generated_dir: Path = self.root_dir / "generated"
        self.static_dir: Path = self.root_dir / "static"
        self.database_path: Path = self.root_dir / "holofabricator.db"
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")

        for directory in (self.upload_dir, self.generated_dir, self.static_dir):
            directory.mkdir(exist_ok=True)


settings = Settings()
