from fastapi import APIRouter, HTTPException

from app.schemas.seo_schema import CannibalizationAuditRequest
from app.services.audit_service import detect_keyword_cannibalization

router = APIRouter(prefix="/api/v1/audit", tags=["Content & Cannibalization Audit"])


@router.post("/cannibalization")
def audit_keyword_cannibalization(payload: CannibalizationAuditRequest):
    """Deteksi potensi saling memakan ranking (Keyword Cannibalization) antar artikel di portal berita BorneoFlash."""
    if len(payload.articles) < 2:
        raise HTTPException(status_code=400, detail="Minimal sertakan 2 artikel untuk diaudit potensi kanibalisasinya.")
    articles_dict = [a.model_dump() if hasattr(a, "model_dump") else a.dict() for a in payload.articles]
    result = detect_keyword_cannibalization(articles_dict)
    return result
