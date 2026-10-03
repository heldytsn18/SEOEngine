import re
from typing import Dict, Any, Tuple, List
import logging

from app.schemas.seo_schema import TaxonomyAnalysisRequest
from app.services.technical_service import clean_text, split_sentences_id
from app.services.ninerouter_service import call_9router_for_taxonomy

logger = logging.getLogger(__name__)


def generate_heuristic_taxonomy_analysis(
    name: str,
    description: str = "",
    taxonomy_type: str = "category"
) -> Dict[str, Any]:
    """Analisis dan generasi SEO taksonomi lokal (heuristic rule-based) tanpa AI."""
    clean_n = name.strip()
    raw_desc = (description or "").strip()
    clean_d = clean_text(raw_desc)
    tax_type = (taxonomy_type or "category").lower()

    # 1. Tentukan Label & Focus Keyword
    if tax_type in ("post_tag", "tag"):
        type_label = "Tag"
        seo_title = f"Kumpulan Berita {clean_n} Terbaru | BorneoFlash"
    elif tax_type in ("newstopic", "topic"):
        type_label = "Topik Khusus"
        seo_title = f"Topik Khusus: {clean_n} Terkini | BorneoFlash"
    else:
        type_label = "Kategori"
        seo_title = f"Berita {clean_n} Terkini Hari Ini | BorneoFlash"

    if len(seo_title) > 60:
        seo_title = seo_title[:57] + "..."

    # Focus Keyword
    lower_n = clean_n.lower()
    focus_kw = lower_n if lower_n.startswith("berita") else f"berita {lower_n}"

    # 2. Meta Description
    if raw_desc and len(raw_desc) >= 50:
        sentences = split_sentences_id(raw_desc)
        meta_desc = ""
        for s in sentences:
            if len(meta_desc) + len(s) + 1 <= 155:
                meta_desc = (meta_desc + " " + s).strip()
            else:
                break
        if not meta_desc:
            meta_desc = raw_desc[:152] + "..." if len(raw_desc) > 155 else raw_desc
    else:
        meta_desc = (
            f"Kumpulan {focus_kw} terbaru dan terlengkap. Simak liputan mendalam, fakta terkini, "
            f"dan peristiwa {clean_n} di BorneoFlash."
        )[:155]

    # 3. Improved Description
    improved_desc = (
        f"Halaman arsip kumpulan {focus_kw}, kabar terkini, dan liputan peristiwa seputar {clean_n}. "
        f"Menyajikan fakta terverifikasi dan ulasan terpercaya untuk pembaca di Kalimantan Timur dan sekitarnya."
    )

    # 4. Scoring & Suggestions
    score = 100
    suggestions: List[str] = []

    # Penilaian Nama
    if len(clean_n) < 3:
        score -= 25
        suggestions.append(f"Nama {type_label} terlalu pendek ({len(clean_n)} karakter). Berikan nama yang lebih deskriptif.")
    elif len(clean_n) > 40:
        score -= 10
        suggestions.append(f"Nama {type_label} terlalu panjang ({len(clean_n)} karakter). Persingkat agar mudah diingat pembaca.")

    # Penilaian Deskripsi
    if not raw_desc:
        score -= 35
        suggestions.append(
            f"Deskripsi {type_label} masih kosong. Tambahkan ringkasan minimal 100 karakter agar halaman arsip memiliki konteks indeks di Google."
        )
    elif len(raw_desc) < 80:
        score -= 15
        suggestions.append(
            f"Deskripsi {type_label} terlalu singkat ({len(raw_desc)} karakter). Kembangkan minimal 100-200 karakter untuk memperkuat SEO."
        )

    # Penilaian Keyword di Deskripsi
    kw_words = [w for w in clean_text(focus_kw).split() if w]
    desc_words = set(clean_d.split())
    if raw_desc and kw_words and not all(w in desc_words for w in kw_words):
        score -= 15
        suggestions.append(
            f"Sisipkan kata kunci target '{focus_kw}' di kalimat pembuka deskripsi agar terdeteksi mesin pencari."
        )

    if not suggestions:
        suggestions.append(f"Halaman arsip {type_label} '{clean_n}' sudah optimal untuk mesin pencari.")

    # Readability Score
    if not raw_desc:
        read_score = 40
    else:
        desc_sentences = split_sentences_id(raw_desc)
        desc_words_count = len(clean_d.split())
        asl = desc_words_count / max(len(desc_sentences), 1)
        if 10 <= asl <= 18:
            read_score = 90
        elif 19 <= asl <= 25:
            read_score = 75
        else:
            read_score = 60

    return {
        "seo_title": seo_title,
        "meta_description": meta_desc,
        "focus_keyword": focus_kw,
        "seo_score": max(0, min(100, score)),
        "readability_score": max(0, min(100, read_score)),
        "suggestions": suggestions,
        "improved_description": improved_desc
    }


def analyze_taxonomy_seo(payload: TaxonomyAnalysisRequest) -> Tuple[Dict[str, Any], str]:
    """Orkestrator analisis SEO taksonomi: Mencoba 9Router AI, fallback ke Heuristik Lokal."""
    name = payload.name.strip()
    desc = (payload.description or "").strip()
    tax_type = (payload.taxonomy_type or "category").strip()

    # 1. Analisis AI via 9Router (jika diaktifkan)
    if payload.use_ai_analysis:
        ai_res = call_9router_for_taxonomy(name, desc, tax_type)
        if ai_res and ai_res.get("seo_title") and ai_res.get("meta_description"):
            # Format output AI
            return {
                "seo_title": str(ai_res.get("seo_title", ""))[:60],
                "meta_description": str(ai_res.get("meta_description", ""))[:160],
                "focus_keyword": str(ai_res.get("focus_keyword", f"berita {name.lower()}")),
                "seo_score": int(ai_res.get("seo_score", 70)),
                "readability_score": int(ai_res.get("readability_score", 75)),
                "suggestions": ai_res.get("suggestions", []),
                "improved_description": str(ai_res.get("improved_description", ""))
            }, "ninerouter"

    # 2. Fallback Heuristik Lokal
    local_res = generate_heuristic_taxonomy_analysis(name, desc, tax_type)
    return local_res, "local"
