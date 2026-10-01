from fastapi import APIRouter, HTTPException

from app.schemas.seo_schema import (
    ArticleAnalysisRequest,
    URLAnalysisRequest,
    SchemaJSONLDRequest,
    TaxonomyAnalysisRequest,
    URLRewriteRequest,
    ContentImprovementRequest
)
from app.services.rewrite_service import rewrite_article_from_url
from app.services.improvement_service import improve_article_content
from app.services.technical_service import (
    analyze_technical_seo,
    extract_focus_keyword_heuristic,
    generate_heuristic_meta
)
from app.services.html_service import analyze_html_structure
from app.services.ninerouter_service import call_9router_for_geo
from app.services.schema_service import generate_newsarticle_jsonld, render_html_snippet
from app.services.taxonomy_service import analyze_taxonomy_seo
from app.services.scraper_service import (
    extract_article_content,
    generate_competitor_opportunities
)

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
        geo_res = call_9router_for_geo(payload.title, payload.content, active_keyword, payload.category or "")
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
    heuristic_meta = generate_heuristic_meta(payload.title, payload.content, active_keyword)
    if geo_res and geo_res.get("seo_title"):
        suggested_title = geo_res.get("seo_title") or payload.title
        suggested_meta = geo_res.get("meta_description") or heuristic_meta["meta_description"]
    else:
        suggested_title = heuristic_meta["seo_title"]
        suggested_meta = heuristic_meta["meta_description"]

    # Perbarui headline_suggestion dengan rekomendasi judul konkret
    if technical_res.get("headline_issues") or technical_res.get("headline_score", 100) < 100:
        technical_res["headline_suggestion"] = f"Gunakan judul alternatif: \"{suggested_title}\""

    # 6. Hitung Agregat Skor Akhir
    tech_score = technical_res.get("seo_score", 0)
    eeat_score = geo_res.get("eeat_score", 0) if geo_res else tech_score
    overall_score = round((tech_score * 0.6) + (eeat_score * 0.4)) if geo_res else tech_score

    all_suggestions = []
    # Berikan rekomendasi judul konkret di urutan teratas jika judul belum ideal
    if technical_res.get("headline_issues") or technical_res.get("headline_score", 100) < 100:
        all_suggestions.append(f"Saran judul: {suggested_title}")
    all_suggestions.extend(technical_res.get("technical_suggestions", []))
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
    """Scrape & analisis URL artikel kompetitor dengan anti-bot header, newspaper4k, dan Beautiful Soup."""
    # 1. Download & parse artikel dari URL dengan browser headers realistis (bypass 403 WAF)
    try:
        extracted = extract_article_content(payload.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengambil artikel dari URL: {str(e)}")

    title = extracted["title"] or ""
    text = extracted["text"] or ""
    html = extracted["html"] or ""

    if not text.strip():
        raise HTTPException(status_code=400, detail="Tidak ada konten teks yang berhasil diekstrak dari URL.")

    # Deteksi apakah URL adalah web internal sendiri atau kompetitor
    domain = extracted["domain"].lower()
    is_own_site = payload.is_own_site
    if is_own_site is None:
        is_own_site = "borneoflash.com" in domain or "localhost" in domain

    active_keyword = (payload.focus_keyword or "").strip()
    meta_keywords = extracted.get("meta_keywords", [])
    geo_res = {}

    # 2. Jalankan Analisis GEO via 9Router (Opsional)
    if payload.use_ai_analysis:
        truncated_text = text[:3000]
        geo_res = call_9router_for_geo(
            title, truncated_text, active_keyword, meta_keywords=meta_keywords, is_own_site=is_own_site
        )

    # 3. Tentukan Kata Kunci yang Dipakai Kompetitor/Halaman & Rekomendasi Kata Kunci Fokus
    detected_competitor_kw = ""
    recommended_focus_kw = ""
    keyword_variations = []

    if not active_keyword:
        # Jika user tidak mengisi keyword, ambil hasil deteksi AI atau fallback heuristik
        detected_competitor_kw = (
            geo_res.get("detected_competitor_keyword")
            or extracted.get("detected_keyword_heuristic")
            or (meta_keywords[0] if meta_keywords else "")
            or extract_focus_keyword_heuristic(title, text)
        ).strip()

        recommended_focus_kw = (
            geo_res.get("focus_keyword")
            or extract_focus_keyword_heuristic(title, text)
        ).strip()

        keyword_variations = geo_res.get("keyword_variations") or (
            meta_keywords[1:4] if len(meta_keywords) > 1 else []
        )

        active_keyword = recommended_focus_kw or detected_competitor_kw
    else:
        # Jika user memasukkan keyword sendiri
        detected_competitor_kw = extracted.get("detected_keyword_heuristic") or (meta_keywords[0] if meta_keywords else "")
        recommended_focus_kw = active_keyword
        keyword_variations = geo_res.get("keyword_variations") or []

    if is_own_site:
        notes_text = (
            f"Kata kunci terdeteksi pada naskah artikel Anda: '{detected_competitor_kw}'. "
            f"Rekomendasi kata kunci fokus terbaik untuk penguatan SEO: '{recommended_focus_kw}'."
            if (detected_competitor_kw and recommended_focus_kw and detected_competitor_kw.lower() != recommended_focus_kw.lower())
            else (
                f"Rekomendasi kata kunci fokus SEO untuk artikel Anda: '{recommended_focus_kw}'."
                if recommended_focus_kw
                else "Kata kunci fokus telah ditentukan oleh pengguna."
            )
        )
    else:
        notes_text = (
            f"Kata kunci terdeteksi yang dibidik kompetitor: '{detected_competitor_kw}'. "
            f"Rekomendasi kata kunci fokus terbaik untuk SEO artikel Anda: '{recommended_focus_kw}'."
            if (detected_competitor_kw and recommended_focus_kw and detected_competitor_kw.lower() != recommended_focus_kw.lower())
            else (
                f"Rekomendasi kata kunci fokus SEO untuk artikel ini: '{recommended_focus_kw}'."
                if recommended_focus_kw
                else "Kata kunci fokus telah ditentukan oleh pengguna."
            )
        )

    keyword_analysis = {
        "user_provided_keyword": payload.focus_keyword or "",
        "detected_competitor_keyword": detected_competitor_kw,
        "recommended_focus_keyword": recommended_focus_kw,
        "meta_keywords_from_page": meta_keywords,
        "keyword_variations": keyword_variations,
        "notes": notes_text
    }

    # 4. Jalankan Analisis Teknis
    technical_res = analyze_technical_seo(title, text, active_keyword)

    # 5. Jalankan Analisis Struktur HTML (Scoped ke Badan Artikel)
    html_res = analyze_html_structure(html, active_keyword, base_url=payload.url, is_own_site=is_own_site)

    heuristic_meta = generate_heuristic_meta(title, text, active_keyword)
    suggested_title = geo_res.get("seo_title") or heuristic_meta["seo_title"]
    suggested_meta = geo_res.get("meta_description") or heuristic_meta["meta_description"]

    # Perbarui headline_suggestion dengan rekomendasi judul konkret
    if technical_res.get("headline_issues") or technical_res.get("headline_score", 100) < 100:
        technical_res["headline_suggestion"] = f"Gunakan judul alternatif: \"{suggested_title}\""

    # 6. Hitung Agregat Skor
    tech_score = technical_res.get("seo_score", 0)
    eeat_score = geo_res.get("eeat_score", 0) if geo_res else tech_score
    overall_score = round((tech_score * 0.6) + (eeat_score * 0.4)) if geo_res else tech_score

    # 7. Peluang Menyalip Kompetitor / Rekomendasi Audit Internal
    opportunities = generate_competitor_opportunities(
        extracted, technical_res, html_res, active_keyword, keyword_analysis=keyword_analysis, is_own_site=is_own_site
    )

    all_suggestions = []
    # Masukkan peluang / rekomendasi di posisi terdepan sebagai rekomendasi strategis
    all_suggestions.extend(opportunities)

    if technical_res.get("headline_issues") or technical_res.get("headline_score", 100) < 100:
        all_suggestions.append(f"Saran judul: {suggested_title}")
    all_suggestions.extend(technical_res.get("technical_suggestions", []))
    all_suggestions.extend(html_res.get("html_suggestions", []))
    if geo_res:
        for component in ("experience", "expertise", "authoritativeness", "trustworthiness"):
            comp_data = geo_res.get(component, {})
            all_suggestions.extend(comp_data.get("suggestions", []))
    all_suggestions = list(dict.fromkeys(all_suggestions))

    # 8. Generate Editor Notes & Suggestions
    editor_notes = geo_res.get("editor_notes") if geo_res and "editor_notes" in geo_res else " ".join(all_suggestions) if all_suggestions else "Artikel sudah cukup baik, tidak ada catatan khusus."

    return {
        "status": "success",
        "data": {
            "news_analysis": technical_res,
            "eeat_analysis": geo_res if geo_res else DEFAULT_EEAT_ANALYSIS,
            "keyword_analysis": keyword_analysis,
            "seo_suggestions": {
                "focus_keyword": recommended_focus_kw or active_keyword,
                "seo_title": suggested_title,
                "meta_description": suggested_meta
            },
            "editor_notes": editor_notes,
            "url_metadata": {
                "url": payload.url,
                "domain": extracted["domain"],
                "is_own_site": is_own_site,
                "title": title,
                "authors": extracted["authors"],
                "publish_date": extracted["publish_date"],
                "top_image": extracted["top_image"],
                "meta_description": extracted["meta_description"],
                "canonical_url": extracted["canonical_url"],
                "word_count": extracted["word_count"],
                "reading_time_minutes": extracted["reading_time_minutes"]
            },
            "competitor_opportunities": opportunities,
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


@router.post("/analyze-taxonomy")
def analyze_taxonomy(payload: TaxonomyAnalysisRequest):
    """Analisis SEO taksonomi berita (kategori, tag, topik khusus) via AI & Heuristik Lokal."""
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Nama taksonomi tidak boleh kosong.")

    result, provider = analyze_taxonomy_seo(payload)
    return {
        "status": "success",
        "data": result,
        "provider": provider
    }


@router.post("/rewrite-url")
def rewrite_url(payload: URLRewriteRequest):
    """Scrape artikel dari URL dan tulis ulang menjadi naskah berita baru yang orisinal, ber-H2, dan ber-SEO tinggi."""
    try:
        result = rewrite_article_from_url(
            url=payload.url,
            focus_keyword=payload.focus_keyword,
            tone=payload.tone or "straight_news",
            local_perspective=payload.local_perspective or "Kalimantan Timur"
        )
        return {
            "status": "success",
            "data": result,
            "provider": "fastapi"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal menulis ulang artikel dari URL: {str(e)}")


@router.post("/improve-content")
def improve_content(payload: ContentImprovementRequest):
    """Perbaiki draf artikel otomatis (Auto-fix) berdasarkan evaluasi teknis SEO & keterbacaan."""
    try:
        result = improve_article_content(
            title=payload.title,
            content=payload.content,
            focus_keyword=payload.focus_keyword,
            mode=payload.mode or "all",
            expand_content=payload.expand_content or False
        )
        return {
            "status": "success",
            "data": result,
            "provider": "fastapi"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal memperbaiki konten artikel: {str(e)}")
