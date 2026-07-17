import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


class FileHandler:
    @staticmethod
    def ensure_upload_dir() -> Path:
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @staticmethod
    def validate_upload(file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")

    @staticmethod
    def save_upload(file: UploadFile) -> tuple[str, str]:
        FileHandler.validate_upload(file)
        upload_dir = FileHandler.ensure_upload_dir()

        file_size = 0
        content = file.file.read()
        file_size = len(content)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

        file_name = Path(file.filename).stem
        extension = Path(file.filename).suffix.lower()
        unique_name = f"{file_name}_{os.urandom(4).hex()}{extension}"
        destination = upload_dir / unique_name
        with destination.open("wb") as buffer:
            buffer.write(content)

        return unique_name, str(destination)
