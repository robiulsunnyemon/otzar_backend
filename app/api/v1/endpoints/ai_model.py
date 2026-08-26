import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.services.cloudinary_service import upload_model_raw_asset
from app.core.config import settings

logger = logging.getLogger("ai_model_service")
router = APIRouter(prefix="/ai", tags=["Neural Model & AI Engine"])

# Live State for Active Neural Model Version
_CURRENT_MODEL_INFO = {
    "version": "v1.0.0",
    "min_app_version": "1.0.0",
    "release_date": "2026-08-26T12:00:00Z",
    "model_name": "Otzar MobileNet-V3 Geological Edge Classifier",
    "model_url": f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/raw/upload/v1/otzar_models/model_v1_0.tflite",
    "labels_url": f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/raw/upload/v1/otzar_models/labels_v1_0.txt",
    "minerals_db_url": f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/raw/upload/v1/otzar_models/minerals_db_v1_0.json",
    "total_classes": 36,
    "size_bytes": 14205000,
    "release_notes": "Initial geological edge classifier for African mineral exploration.",
    "is_mandatory": False,
}


def _auto_increment_version(current_ver: str) -> str:
    """
    Automatically increments version number (e.g. v1.0.0 -> v1.1.0 -> v1.2.0)
    so administrators don't have to manually type or risk mistakes.
    """
    try:
        clean = current_ver.strip().lstrip("v")
        parts = [int(p) for p in clean.split(".")]
        if len(parts) >= 2:
            parts[1] += 1
            if len(parts) >= 3:
                parts[2] = 0
            return f"v{'.'.join(str(p) for p in parts)}"
        elif len(parts) == 1:
            return f"v{parts[0] + 1}.0.0"
    except Exception:
        pass
    return f"v{current_ver}_next"


@router.get(
    "/neural-model-latest",
    summary="Get Latest Active Neural Model Version & Download URLs",
    description="Returns current active AI edge model metadata for Over-The-Air (OTA) background sync.",
)
async def get_latest_neural_model():
    return {
        "status": "success",
        "data": _CURRENT_MODEL_INFO,
    }


@router.post(
    "/publish-model-files",
    summary="Directly Upload Model Files (.tflite, .txt, .json) & Auto-Increment Version",
    description="Upload raw model files directly to Cloudinary CDN and automatically upgrade all devices Over-The-Air without manual version typing.",
)
async def publish_model_files(
    model_file: Optional[UploadFile] = File(None, description="The .tflite neural model file"),
    labels_file: Optional[UploadFile] = File(None, description="The labels.txt file containing mineral names"),
    minerals_db_file: Optional[UploadFile] = File(None, description="The minerals_db.json geological database file"),
    release_notes: Optional[str] = Form(None, description="What's new in this AI model update"),
    custom_version: Optional[str] = Form(None, description="Optional custom version string (leave empty for automatic increment)"),
):
    """
    1. Auto-increments the model version safely.
    2. Uploads all provided files directly to Cloudinary CDN under otzar_models.
    3. Updates live model state to broadcast to all connected mobile clients.
    """
    # 1. Compute Safe Auto-Incremented Version
    current_version = _CURRENT_MODEL_INFO.get("version", "v1.0.0")
    new_version = custom_version.strip() if (custom_version and custom_version.strip()) else _auto_increment_version(current_version)

    uploaded_assets = {}

    # 2. Upload .tflite model file if provided
    if model_file and model_file.filename:
        url = await upload_model_raw_asset(
            file=model_file,
            asset_type="model",
            version_tag=new_version,
        )
        if url:
            _CURRENT_MODEL_INFO["model_url"] = url
            uploaded_assets["model"] = url

    # 3. Upload labels.txt file if provided
    if labels_file and labels_file.filename:
        url = await upload_model_raw_asset(
            file=labels_file,
            asset_type="labels",
            version_tag=new_version,
        )
        if url:
            _CURRENT_MODEL_INFO["labels_url"] = url
            uploaded_assets["labels"] = url

    # 4. Upload minerals_db.json file if provided
    if minerals_db_file and minerals_db_file.filename:
        url = await upload_model_raw_asset(
            file=minerals_db_file,
            asset_type="minerals_db",
            version_tag=new_version,
        )
        if url:
            _CURRENT_MODEL_INFO["minerals_db_url"] = url
            uploaded_assets["minerals_db"] = url

    # 5. Update Version Metadata
    _CURRENT_MODEL_INFO["version"] = new_version
    _CURRENT_MODEL_INFO["release_date"] = datetime.now(timezone.utc).isoformat()
    if release_notes:
        _CURRENT_MODEL_INFO["release_notes"] = release_notes
    else:
        _CURRENT_MODEL_INFO["release_notes"] = f"Automated AI Model Upgrade ({new_version})"

    return {
        "status": "success",
        "message": f"Successfully published Neural Model {new_version} to Cloudinary CDN!",
        "new_version": new_version,
        "previous_version": current_version,
        "uploaded_assets": uploaded_assets,
        "active_model_data": _CURRENT_MODEL_INFO,
    }


@router.post(
    "/update-model-version",
    summary="Update Active Model Version Metadata Manually",
    description="Allows administrators to manually set model metadata URLs.",
)
async def update_model_version(
    version: Optional[str] = Form(None),
    model_url: Optional[str] = Form(None),
    labels_url: Optional[str] = Form(None),
    minerals_db_url: Optional[str] = Form(None),
    release_notes: Optional[str] = Form(None),
):
    if version:
        _CURRENT_MODEL_INFO["version"] = version
    if model_url:
        _CURRENT_MODEL_INFO["model_url"] = model_url
    if labels_url:
        _CURRENT_MODEL_INFO["labels_url"] = labels_url
    if minerals_db_url:
        _CURRENT_MODEL_INFO["minerals_db_url"] = minerals_db_url
    if release_notes:
        _CURRENT_MODEL_INFO["release_notes"] = release_notes

    return {
        "status": "success",
        "data": _CURRENT_MODEL_INFO,
    }
