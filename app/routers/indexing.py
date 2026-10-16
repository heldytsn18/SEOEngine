from fastapi import APIRouter, HTTPException

from app.schemas.seo_schema import (
    IndexingNotificationRequest,
    IndexingBatchRequest
)
from app.services.indexing_service import (
    send_google_indexing_notification,
    batch_google_indexing_notifications,
    check_indexing_credentials_status
)

router = APIRouter(prefix="/api/v1/indexing", tags=["Google Instant Indexing"])


@router.get("/status")
def get_indexing_status():
    """Cek status konfigurasi Google Service Account JSON untuk Google Instant Indexing API."""
    return check_indexing_credentials_status()


@router.post("/notify")
def notify_google_indexing(payload: IndexingNotificationRequest):
    """Kirim notifikasi instan ke Google Indexing API agar artikel berita segera dirayapi Googlebot (1-5 menit setelah tayang)."""
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="URL artikel wajib diisi.")
    result = send_google_indexing_notification(payload.url, action=payload.action or "URL_UPDATED")
    return result


@router.post("/batch")
def batch_notify_google_indexing(payload: IndexingBatchRequest):
    """Kirim notifikasi perayapan instan ke Google Indexing API untuk beberapa URL berita sekaligus."""
    if not payload.urls:
        raise HTTPException(status_code=400, detail="Daftar URL berita tidak boleh kosong.")
    result = batch_google_indexing_notifications(payload.urls, action=payload.action or "URL_UPDATED")
    return result
