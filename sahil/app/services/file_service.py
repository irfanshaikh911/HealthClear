import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "application/pdf": "pdf",
}


async def save_upload(file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Only JPG, JPEG, PDF allowed.")

    ext = ALLOWED_MIME_TYPES[file.content_type]
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB.")

    bill_uuid = str(uuid.uuid4())
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{bill_uuid}.{ext}")

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)

    return {
        "bill_uuid": bill_uuid,
        "file_path": file_path,
        "file_type": ext,
        "original_filename": file.filename,
    }
