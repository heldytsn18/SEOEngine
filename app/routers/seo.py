from fastapi import APIRouter, HTTPException

from app.schemas.seo_schema import ArticleAnalysisRequest, URLAnalysisRequest, SchemaJSONLDRequest
from app.services.technical_service import analyze_technical_seo
from app.services.html_service import analyze_html_structure
from app.services.ninerouter_service import call_9router_for_geo
from app.services.schema_service import generate_newsarticle_jsonld, render_html_snippet

router = APIRouter(prefix="/api/v1/seo", tags=["SEO Engine"])


@router.post("/analyze")
def analyze_article(payload: ArticleAnalysisRequest):
    """Analisis draf artikel: teknis SEO + struktur HTML + GEO/E-E-A-T."""
    # 1. Jalankan Analisis Teknis Lokal (Sastrawi + Rule-Based)
    technical_res = analyze_technical_seo(payload.title, payload.content, payload.focus_keyword)

    if "error" in technical_res:
        raise HTTPException(status_code=400, detail=technical_res["error"])

    # 2. Jalankan Analisis Struktur HTML
    html_res = analyze_html_structure(payload.content, payload.focus_keyword)

    # 3. Jalankan Analisis GEO via 9Router (Opsional)
    geo_res = {}
    if payload.use_ai_analysis:
        geo_res = call_9router_for_geo(payload.title, payload.content, payload.focus_keyword)

    # 4. Hitung Agregat Skor Akhir
    tech_score = technical_res.get("seo_score", 0)
    eeat_score = geo_res.get("eeat_score", 0) if geo_res else tech_score
    overall_score = round((tech_score * 0.6) + (eeat_score * 0.4)) if geo_res else tech_score

    all_suggestions = technical_res.get("technical_suggestions", [])[:]
    all_suggestions.extend(html_res.get("html_suggestions", []))
    if geo_res:
        for component in ("experience", "expertise", "authoritativeness", "trustworthiness"):
            comp_data = geo_res.get(component, {})
            all_suggestions.extend(comp_data.get("suggestions", []))
    # Hapus duplikasi, pertahankan urutan
    all_suggestions = list(dict.fromkeys(all_suggestions))

    # 5. Generate Editor Notes
    editor_notes = geo_res.get("editor_notes") if geo_res and "editor_notes" in geo_res else " ".join(all_suggestions) if all_suggestions else "Artikel sudah cukup baik, tidak ada catatan khusus."

    return {
        "status": "success",
        "data": {
            "news_analysis": technical_res,
            "eeat_analysis": geo_res if geo_res else {
                "eeat_score": 0,
                "experience": { "score": 0, "has_firsthand_experience": False, "suggestions": [] },
                "expertise": { "score": 0, "has_expert_sources": False, "has_data_statistics": False, "suggestions": [] },
                "authoritativeness": { "score": 0, "has_official_sources": False, "has_citations": False, "suggestions": [] },
                "trustworthiness": { "score": 0, "is_balanced": False, "has_verification": False, "suggestions": [] }
            },
            "seo_suggestions": {
                "focus_keyword": payload.focus_keyword,
                "seo_title": payload.title,
                "meta_description": payload.content[:150] + "..." if payload.content else ""
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

    # 2. Jalankan Analisis Teknis
    technical_res = analyze_technical_seo(title, text, payload.focus_keyword)

    # 3. Jalankan Analisis Struktur HTML
    html_res = analyze_html_structure(html, payload.focus_keyword, base_url=payload.url)

    # 4. Jalankan Analisis GEO via 9Router (Opsional)
    geo_res = {}
    if payload.use_ai_analysis:
        # Batasi konten ke 3000 karakter agar tidak terlalu besar untuk prompt AI
        truncated_text = text[:3000]
        geo_res = call_9router_for_geo(title, truncated_text, payload.focus_keyword)

    # 5. Hitung Agregat Skor
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

    # 6. Generate Editor Notes
    editor_notes = geo_res.get("editor_notes") if geo_res and "editor_notes" in geo_res else " ".join(all_suggestions) if all_suggestions else "Artikel sudah cukup baik, tidak ada catatan khusus."

    return {
        "status": "success",
        "data": {
            "news_analysis": technical_res,
            "eeat_analysis": geo_res if geo_res else {
                "eeat_score": 0,
                "experience": { "score": 0, "has_firsthand_experience": False, "suggestions": [] },
                "expertise": { "score": 0, "has_expert_sources": False, "has_data_statistics": False, "suggestions": [] },
                "authoritativeness": { "score": 0, "has_official_sources": False, "has_citations": False, "suggestions": [] },
                "trustworthiness": { "score": 0, "is_balanced": False, "has_verification": False, "suggestions": [] }
            },
            "seo_suggestions": {
                "focus_keyword": payload.focus_keyword,
                "seo_title": title,
                "meta_description": text[:150] + "..." if text else ""
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
