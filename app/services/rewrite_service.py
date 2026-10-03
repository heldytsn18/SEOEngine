import re
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import logging

from app.services.ninerouter_service import (
    NINEROUTER_API_KEY,
    NINEROUTER_URL,
    NINEROUTER_MODEL,
    NINEROUTER_TIMEOUT
)
from app.services.scraper_service import extract_article_content
from app.services.technical_service import (
    analyze_technical_seo,
    extract_focus_keyword_heuristic,
    clean_text
)

logger = logging.getLogger(__name__)


def calculate_text_similarity(original_text: str, rewritten_text: str) -> float:
    """Menghitung persentase kemiripan teks menggunakan Jaccard 3-gram (3-word shingles)."""
    words_orig = re.findall(r'\b\w+\b', original_text.lower())
    words_rewritten = re.findall(r'\b\w+\b', rewritten_text.lower())

    if len(words_orig) < 3 or len(words_rewritten) < 3:
        s1 = set(words_orig)
        s2 = set(words_rewritten)
        if not s1 or not s2:
            return 0.0
        return round((len(s1.intersection(s2)) / len(s1.union(s2))) * 100, 1)

    shingles_orig = set(' '.join(words_orig[i:i+3]) for i in range(len(words_orig) - 2))
    shingles_rewritten = set(' '.join(words_rewritten[i:i+3]) for i in range(len(words_rewritten) - 2))

    intersection = len(shingles_orig.intersection(shingles_rewritten))
    union = len(shingles_orig.union(shingles_rewritten))
    if union == 0:
        return 0.0
    return round((intersection / union) * 100, 1)


def rewrite_article_from_url(
    url: str,
    focus_keyword: Optional[str] = None,
    tone: str = "straight_news",
    local_perspective: str = "Kalimantan Timur"
) -> Dict[str, Any]:
    """Mengambil naskah dari URL, lalu menulis ulang menjadi artikel berita baru berstandar SEO tinggi."""
    # 1. Scrape & parse artikel sumber
    extracted = extract_article_content(url)
    source_title = extracted.get("title") or ""
    source_text = extracted.get("text") or ""
    meta_keywords = extracted.get("meta_keywords", [])

    if not source_text.strip():
        raise Exception("Tidak ada konten teks yang dapat diekstrak dari URL target.")

    # 2. Tentukan target focus keyword
    target_keyword = (focus_keyword or "").strip()
    if not target_keyword:
        target_keyword = (
            extracted.get("detected_keyword_heuristic") or
            (meta_keywords[0] if meta_keywords else "") or
            extract_focus_keyword_heuristic(source_title, source_text)
        ).strip()

    current_date = datetime.now().strftime("%Y-%m-%d")
    source_domain = extracted.get("domain", "")

    # 3. Prompt Jurnalisme & SEO ke 9Router AI
    tone_instructions = {
        "straight_news": "Gaya berita langsung (straight news/hard news) yang padat, lugas, faktual, dan objektif.",
        "investigative": "Gaya investigatif mendalam yang menggali konteks, sebab-akibat, dan keakuratan fakta.",
        "feature": "Gaya human-interest/feature yang bertutur mengalir, deskriptif, dan memikat pembaca.",
        "press_release": "Gaya rilis pers profesional yang mengedepankan informasi inti, pernyataan resmi, dan data."
    }
    selected_tone = tone_instructions.get(tone, tone_instructions["straight_news"])

    prompt = f"""
Bertindaklah sebagai Senior News Editor & Jurnalis Berita Indonesia terkemuka untuk media daring.
Tugas Anda: Tulis ulang (rewrite) artikel berita berikut menjadi naskah berita BARU yang orisinal, kaya informasi, dan berstandar SEO tinggi untuk redaksi portal berita.

Konteks Waktu: Hari ini adalah tanggal {current_date}. Jangan anggap tahun berjalan sebagai masa depan.
Perspektif Wilayah: Prioritaskan relevansi untuk wilayah {local_perspective} jika ada keterkaitan peristiwa.
Gaya Penulisan: {selected_tone}

Data Berita Asal:
- Judul Asal: {source_title}
- Kata Kunci Fokus Target: "{target_keyword}"
- Sumber Asal: {source_domain}
- Isi Berita Asal:
{source_text[:2500]}

ATURAN STRUKTUR & JURNALISME:
1. Piramida Terbalik: Paragraf pembuka (lede) wajib merangkum fakta utama 5W1H (Siapa, Apa, Kapan, Di mana, Mengapa, Bagaimana) secara padat dan menarik.
2. Penempatan Keyword: Sisipkan frasa kunci "{target_keyword}" di judul, di paragraf pembuka (50 kata pertama), dan di minimal 1 subheading H2.
3. Subheading: Bagi badan berita menjadi 2 sampai 3 bagian menggunakan tag HTML <h2>. Contoh: <h2>Dinamika Pemilihan di Senat Tertutup</h2>.
4. Format Isi: Tulis naskah dalam format tag HTML rapi (<p> untuk paragraf berita dan <h2> untuk subjudul). Jangan gunakan tag <h1> atau <h3>.
5. Panjang Naskah: Kembangkan naskah berita menjadi 350 hingga 600 kata dengan kalimat-kalimat efektif (hindari kalimat berbelit > 25 kata).
6. Anti-Plagiarisme: Susun ulang kalimat dengan sudut pandang redaksi sendiri, jangan menyalin kalimat asal mentah-mentah.
7. Judul: Buat 1 judul utama optimal (50-65 karakter) yang memikat klik dan memuat kata kunci fokus, serta berikan 2-3 judul alternatif.
8. Meta Description: Buat ringkasan padat 130-150 karakter yang memancing klik di hasil pencarian Google.
9. Taksonomi: Rekomendasikan 1 nama kategori rubrik berita (contoh: Pendidikan, Daerah, Ekonomi, Politik) dan 4-6 tag relevan.

Berikan output JSON SAJA tanpa markdown block atau teks pembuka, dengan format persis:
{{
  "title": "<Judul utama SEO optimal 50-65 karakter>",
  "title_alternatives": [
    "<Judul alternatif sudut pandang 1>",
    "<Judul alternatif sudut pandang 2>",
    "<Judul alternatif sudut pandang 3>"
  ],
  "lede": "<Paragraf pembuka 5W1H lengkap dengan kata kunci>",
  "content_html": "<p>Paragraf lede...</p><h2>Subjudul 1</h2><p>Paragraf naskah...</p><h2>Subjudul 2</h2><p>Paragraf penutup...</p>",
  "content_plain": "<Naskah teks bersih tanpa HTML, dipisahkan baris baru ganda per paragraf>",
  "focus_keyword": "{target_keyword}",
  "keyword_variations": ["<variasi keyword 1>", "<variasi keyword 2>", "<variasi keyword 3>"],
  "meta_description": "<Meta description ringkas dan padat 130-150 karakter>",
  "suggested_category": "<Nama Kategori>",
  "suggested_tags": ["<Tag 1>", "<Tag 2>", "<Tag 3>", "<Tag 4>"]
}}
"""

    ai_data = None
    try:
        headers = {
            "Authorization": f"Bearer {NINEROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": NINEROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "stream": False
        }
        res = requests.post(NINEROUTER_URL, headers=headers, json=payload, timeout=NINEROUTER_TIMEOUT)
        if res.status_code == 200:
            resp_json = res.json()
            raw_ai = resp_json["choices"][0]["message"]["content"]
            # Bersihkan markdown code fences
            clean_json = re.sub(r'```(?:json)?\s*|\s*```', '', raw_ai).strip()
            try:
                ai_data = json.loads(clean_json)
            except Exception:
                # Fallback: cari blok {...} menggunakan regex
                match = re.search(r'(\{[\s\S]*\})', clean_json)
                if match:
                    ai_data = json.loads(match.group(1))
    except Exception as e:
        logger.exception("9Router rewrite call failed, using heuristic fallback")
        ai_data = None
    if not ai_data:
        ai_data = {
            "title": f"Liputan Terkini: {source_title[:50]}",
            "title_alternatives": [source_title],
            "lede": source_text[:200] + "...",
            "content_html": f"<p>{source_text[:300]}</p><h2>Informasi Terkait</h2><p>{source_text[300:700]}</p>",
            "content_plain": source_text[:700],
            "focus_keyword": target_keyword,
            "keyword_variations": meta_keywords[1:4] if len(meta_keywords) > 1 else [],
            "meta_description": source_text[:140] + "...",
            "suggested_category": "Berita",
            "suggested_tags": meta_keywords[:4] if meta_keywords else ["Berita Terkini"]
        }

    rewritten_title = ai_data.get("title", source_title)
    rewritten_html = ai_data.get("content_html", "")
    rewritten_plain = ai_data.get("content_plain", "")
    if not rewritten_plain and rewritten_html:
        rewritten_plain = re.sub(r'<[^>]+>', ' ', rewritten_html)
        rewritten_plain = re.sub(r'\s+', ' ', rewritten_plain).strip()

    # 4. Evaluasi Teknis SEO & Readability pada Naskah Baru
    tech_eval = analyze_technical_seo(rewritten_title, rewritten_plain, target_keyword)

    # 5. Cek Kemiripan Teks dengan Naskah Asal (Anti-Plagiarism)
    similarity_pct = calculate_text_similarity(source_text, rewritten_plain)
    if similarity_pct < 20.0:
        orig_status = "Sangat Aman (Bebas Plagiarisme / Orisinalitas Sangat Tinggi)"
    elif similarity_pct <= 35.0:
        orig_status = "Cukup Aman (Parafrase Baik / Orisinalitas Standar)"
    else:
        orig_status = "Perlu Ditinjau (Kemiripan Cukup Tinggi dengan Naskah Asal)"

    words = rewritten_plain.split()
    word_count = len(words)
    reading_time = max(1, round(word_count / 180))

    # 6. Format Atribusi Sumber Sesuai Etika Jurnalistik
    domain_clean = source_domain.replace("www.", "")
    attribution_quote = f"Disadur dari pemberitaan {domain_clean} dengan sudut pandang redaksional BorneoFlash."

    return {
        "article": {
            "title": rewritten_title,
            "title_alternatives": ai_data.get("title_alternatives", []),
            "lede": ai_data.get("lede", ""),
            "content": rewritten_html,
            "content_plain": rewritten_plain,
            "word_count": word_count,
            "reading_time_minutes": reading_time
        },
        "seo_metadata": {
            "focus_keyword": ai_data.get("focus_keyword", target_keyword),
            "keyword_variations": ai_data.get("keyword_variations", []),
            "meta_description": ai_data.get("meta_description", ""),
            "suggested_category": ai_data.get("suggested_category", "Daerah"),
            "suggested_tags": ai_data.get("suggested_tags", [])
        },
        "quality_metrics": {
            "seo_score": tech_eval.get("seo_score", 0),
            "readability_score": tech_eval.get("readability_score", 0),
            "similarity_percentage": similarity_pct,
            "originality_status": orig_status,
            "technical_issues": tech_eval.get("headline_issues", []) + tech_eval.get("technical_suggestions", [])[:2]
        },
        "source_metadata": {
            "source_url": url,
            "source_domain": source_domain,
            "source_title": source_title,
            "original_word_count": extracted.get("word_count", 0),
            "attribution_quote": attribution_quote
        }
    }
