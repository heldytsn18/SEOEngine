from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from app.schemas.seo_schema import (
    TrendingTopicsResponse,
    AutocompleteRequest,
    PeopleAlsoAskRequest,
    CompareTrendsRequest
)
from app.services.trends_service import (
    fetch_daily_trends,
    fetch_google_autocomplete,
    fetch_people_also_ask,
    compare_keyword_trends
)

router = APIRouter(prefix="/api/v1/trends", tags=["Google Trends & Autocomplete"])


@router.get("/daily")
def get_daily_trends(geo: str = Query("ID", description="Kode negara (default: ID untuk Indonesia)")):
    """Ambil topik pencarian terhangat hari ini dari Google Trends RSS feed resmi secara real-time.
    
    Menampilkan perkiraan traffic, ringkasan berita pemicu, dan sumber berita rujukan.
    """
    items = fetch_daily_trends(geo=geo)
    return {
        "status": "success",
        "geo": geo.upper(),
        "total": len(items),
        "items": items
    }


@router.get("/autocomplete")
def get_autocomplete(
    q: str = Query(..., description="Kueri kata kunci pencarian awal"),
    geo: str = Query("ID", description="Kode negara"),
    lang: str = Query("id", description="Kode bahasa")
):
    """Ambil rekomendasi kueri yang sedang aktif diketik pengguna di Google Search (Google Suggest API)."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Parameter pencarian 'q' wajib diisi.")
    suggestions = fetch_google_autocomplete(q, geo=geo, lang=lang)
    return {
        "status": "success",
        "query": q.strip(),
        "total": len(suggestions),
        "suggestions": suggestions
    }


@router.get("/questions")
def get_people_also_ask(
    keyword: str = Query(..., description="Kata kunci utama artikel berita"),
    geo: str = Query("ID", description="Kode negara")
):
    """Ambil daftar pertanyaan populer publik di Google (People Also Ask) berbasis formula 5W+1H Indonesia."""
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="Parameter 'keyword' wajib diisi.")
    questions = fetch_people_also_ask(keyword, geo=geo)
    return {
        "status": "success",
        "keyword": keyword.strip(),
        "total": len(questions),
        "questions": questions
    }


@router.post("/compare")
def compare_trends(payload: CompareTrendsRequest):
    """Bandingkan search demand dan kueri turunan antara 2 hingga 5 kata kunci alternatif untuk memilih kata kunci terbaik."""
    if len(payload.keywords) < 2:
        raise HTTPException(status_code=400, detail="Minimal sertakan 2 kata kunci untuk dibandingkan.")
    res = compare_keyword_trends(payload.keywords, geo=payload.geo or "ID")
    return res
