"""Deterministic local document intake; OCR and AI are intentionally excluded."""

from .upload_manager import IncomingUpload, UploadManager
from .upload_manifest import UploadManifest

__all__ = ["IncomingUpload", "UploadManager", "UploadManifest"]
