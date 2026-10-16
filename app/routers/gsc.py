from fastapi import APIRouter, HTTPException

from app.schemas.seo_schema import (
    GSCPerformanceRequest,
    GSCOpportunitiesRequest
)
from app.services.gsc_service import (
    get_gsc_url_performance,
    get_gsc_low_hanging_fruits,
    check_gsc_credentials_status
)

router = APIRouter(prefix="/api/v1/gsc", tags=["Google Search Console"])


@router.get("/status")
def get_gsc_status():
    """Periksa status konfigurasi kredensial Google Search Console API."""
    return check_gsc_credentials_status()


@router.post("/url-performance")
def get_url_performance(payload: GSCPerformanceRequest):
    """Ambil data performa riil artikel dari Google Search Console (Total Klik, Impresi, CTR, dan Rata-rata Posisi Ranking)."""
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="URL artikel wajib diisi.")
    result = get_gsc_url_performance(payload.url, days=payload.days or 28)
    return result


@router.post("/opportunities")
def get_optimization_opportunities(payload: GSCOpportunitiesRequest):
    """Temukan peluang optimasi artikel BorneoFlash (Low-Hanging Fruits):
    
    Kueri dengan impresi tinggi di halaman 1-2 Google tapi CTR masih rendah, siap didorong naik dengan revisi judul/meta.
    """
    result = get_gsc_low_hanging_fruits(
        site_url=payload.site_url,
        days=payload.days or 28,
        min_impressions=payload.min_impressions or 100,
        max_ctr=payload.max_ctr or 0.05
    )
    return result
