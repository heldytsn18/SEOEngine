from fastapi import APIRouter, HTTPException

from app.schemas.seo_schema import ArticleAnalysisRequest, URLAnalysisRequest, SchemaJSONLDRequest
from app.services.technical_service import (
    analyze_technical_seo,
    extract_focus_keyword_heuristic,
    generate_heuristic_meta
)
from app.services.html_service import analyze_html_structure
from app.services.ninerouter_service import call_9router_for_geo
from app.services.schema_service import generate_newsarticle_jsonld, render_html_snippet

router = APIRouter(prefix="/api/v1/seo", tags=["SEO Engine"])

DEFAULT_EEAT_ANALYSIS = {
    "eeat_score": 0,
    "experience": { "score": 0, "has_firsthand_experience": False, "suggestions": [] },
    "expertise": { "score": 0, "has_expert_sources": False, "has_data_statistics": False, "suggestions": [] },
    "authoritativeness": { "score": 0, "has_official_sources": False, "has_citations": False, "suggestions": [] },
    "trustworthiness": { "score": 0, "is_balanced": False, "has_verification": False, "suggestions": [] }
}


@router.post("/analyze")
def analyze_article(payload: ArticleAnalysisRequest):
    """Analisis draf artikel: Generate metadata -> teknis SEO + struktur HTML + GEO/E-E-A-T."""
    active_keyword = (payload.focus_keyword or "").strip()
    geo_res = {}

    # 1. Jalankan Analisis GEO via 9Router (AI juga menghasilkan focus_keyword, seo_title, meta_description)
    if payload.use_ai_analysis:
        geo_res = call_9router_for_geo(payload.title, payload.content, active_keyword)
        # Jika keyword awal kosong tapi AI berhasil generate focus_keyword, gunakan hasil AI
        if not active_keyword and geo_res.get("focus_keyword"):
            active_keyword = geo_res["focus_keyword"].strip()

    # 2. Jika keyword masih kosong (AI nonaktif atau gagal), gunakan ekstraksi heuristik lokal
    if not active_keyword:
        active_keyword = extract_focus_keyword_heuristic(payload.title, payload.content)

    # 3. Jalankan Analisis Teknis Lokal (Sastrawi + Rule-Based) menggunakan active_keyword
    technical_res = analyze_technical_seo(payload.title, payload.content, active_keyword)
    if "error" in technical_res:
        raise HTTPException(status_code=400, detail=technical_res["error"])

    # 4. Jalankan Analisis Struktur HTML
    html_res = analyze_html_structure(payload.content, active_keyword, base_url=payload.base_url)

    # 5. Tentukan saran SEO (prioritaskan hasil AI jika ada, fallback ke heuristik lokal)
    if geo_res and geo_res.get("seo_title"):
        suggested_title = geo_res.get("seo_title") or payload.title
        suggested_meta = geo_res.get("meta_description") or (payload.content[:150] + "..." if payload.content else "")
    else:
        heuristic_meta = generate_heuristic_meta(payload.title, payload.content, active_keyword)
        suggested_title = heuristic_meta["seo_title"]
        suggested_meta = heuristic_meta["meta_description"]

    # 6. Hitung Agregat Skor Akhir
    tech_score = technical_res.get("seo_score", 0)
    eeat_score = geo_res.get("eeat_score", 0) if geo_res else tech_score
    overall_score = round((tech_score * 0.6) + (eeat_score * 0.4)) if geo_res else tech_score

    all_suggestions = technical_res.get("technical_suggestions", [])[:]
    all_suggestions.extend(html_res.get("html_suggestions", []))
    if geo_res:
        for component in ("experience", "expertise", "authoritativeness", "trustworthiness"):
            comp_data = geo_res.get(component, {})
            all_suggestions.extend(comp_data.get("suggestions", []))
    all_suggestions = list(dict.fromkeys(all_suggestions))

    # 7. Generate Editor Notes
    editor_notes = geo_res.get("editor_notes") if geo_res and "editor_notes" in geo_res else " ".join(all_suggestions) if all_suggestions else "Artikel sudah cukup baik, tidak ada catatan khusus."

    return {
        "status": "success",
        "data": {
            "news_analysis": technical_res,
            "eeat_analysis": geo_res if geo_res else DEFAULT_EEAT_ANALYSIS,
            "seo_suggestions": {
                "focus_keyword": active_keyword,
                "seo_title": suggested_title,
                "meta_description": suggested_meta
            },
            "editor_notes": editor_notes,
            "overall_score": overall_score,
            "html_structure_analysis": html_res,
            "combined_suggestions": all_suggestions
        },
        "provider": "fastapi"
    }


@router.post("/analyze-url")
def analyze_url(payload: URLAnalysisRequest):
    """Scrape & analisis URL artikel kompetitor menggunakan newspaper4k."""
    try:
        from newspaper import Article
    except ImportError:
        raise HTTPException(status_code=500, detail="Library newspaper4k belum terinstal.")

    # 1. Download & parse artikel dari URL
    try:
        article = Article(payload.url)
        article.download()
        article.parse()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengambil artikel dari URL: {str(e)}")

    title = article.title or ""
    text = article.text or ""
    html = article.html or ""
    authors = article.authors or []
    publish_date = str(article.publish_date) if article.publish_date else None
    top_image = article.top_image or ""

    if not text.strip():
        raise HTTPException(status_code=400, detail="Tidak ada konten teks yang berhasil diekstrak dari URL.")

    active_keyword = (payload.focus_keyword or "").strip()
    geo_res = {}

    # 2. Jalankan Analisis GEO via 9Router (Opsional)
    if payload.use_ai_analysis:
        truncated_text = text[:3000]
        geo_res = call_9router_for_geo(title, truncated_text, active_keyword)
        if not active_keyword and geo_res.get("focus_keyword"):
            active_keyword = geo_res["focus_keyword"].strip()

    # 3. Fallback jika keyword masih kosong
    if not active_keyword:
        active_keyword = extract_focus_keyword_heuristic(title, text)

    # 4. Jalankan Analisis Teknis
    technical_res = analyze_technical_seo(title, text, active_keyword)

    # 5. Jalankan Analisis Struktur HTML
    html_res = analyze_html_structure(html, active_keyword, base_url=payload.url)

    # 6. Hitung Agregat Skor
    tech_score = technical_res.get("seo_score", 0)
    eeat_score = geo_res.get("eeat_score", 0) if geo_res else tech_score
    overall_score = round((tech_score * 0.6) + (eeat_score * 0.4)) if geo_res else tech_score

    all_suggestions = technical_res.get("technical_suggestions", [])[:]
    all_suggestions.extend(html_res.get("html_suggestions", []))
    if geo_res:
        for component in ("experience", "expertise", "authoritativeness", "trustworthiness"):
            comp_data = geo_res.get(component, {})
            all_suggestions.extend(comp_data.get("suggestions", []))
    all_suggestions = list(dict.fromkeys(all_suggestions))

    # 7. Generate Editor Notes & Suggestions
    editor_notes = geo_res.get("editor_notes") if geo_res and "editor_notes" in geo_res else " ".join(all_suggestions) if all_suggestions else "Artikel sudah cukup baik, tidak ada catatan khusus."

    suggested_title = geo_res.get("seo_title") or title
    suggested_meta = geo_res.get("meta_description") or (text[:150] + "..." if text else "")

    return {
        "status": "success",
        "data": {
            "news_analysis": technical_res,
            "eeat_analysis": geo_res if geo_res else DEFAULT_EEAT_ANALYSIS,
            "seo_suggestions": {
                "focus_keyword": active_keyword,
                "seo_title": suggested_title,
                "meta_description": suggested_meta
            },
            "editor_notes": editor_notes,
            "url_metadata": {
                "url": payload.url,
                "title": title,
                "authors": authors,
                "publish_date": publish_date,
                "top_image": top_image
            },
            "overall_score": overall_score,
            "html_structure_analysis": html_res,
            "combined_suggestions": all_suggestions
        },
        "provider": "fastapi"
    }


@router.post("/schema-jsonld")
def create_schema_jsonld(payload: SchemaJSONLDRequest):
    """Generate NewsArticle Schema.org JSON-LD yang valid untuk Google News."""
    schema = generate_newsarticle_jsonld(payload)
    html_snippet = render_html_snippet(schema)

    return {
        "status": "success",
        "data": {
            "jsonld": schema,
            "html_snippet": html_snippet
        }
    }
