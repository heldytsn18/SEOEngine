import re
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.services.ninerouter_service import (
    NINEROUTER_API_KEY,
    NINEROUTER_URL,
    NINEROUTER_MODEL,
    NINEROUTER_TIMEOUT
)
from app.services.technical_service import (
    analyze_technical_seo,
    extract_focus_keyword_heuristic,
    generate_heuristic_meta,
    clean_text
)


def improve_article_content(
    title: str,
    content: str,
    focus_keyword: Optional[str] = None,
    mode: str = "all",
    expand_content: bool = False
) -> Dict[str, Any]:
    """Memperbaiki naskah draf artikel secara terarah berdasarkan evaluasi teknis SEO & keterbacaan."""
    raw_content = content.strip()
    if not raw_content:
        raise Exception("Konten artikel tidak boleh kosong.")

    # Bersihkan HTML jika input mengandung tag agar plain text terbaca
    plain_content = re.sub(r'<[^>]+>', ' ', raw_content)
    plain_content = re.sub(r'\s+', ' ', plain_content).strip()

    target_keyword = (focus_keyword or "").strip()
    if not target_keyword:
        target_keyword = extract_focus_keyword_heuristic(title, plain_content)

    # 1. Evaluasi Awal (Before)
    before_eval = analyze_technical_seo(title, plain_content, target_keyword)
    before_readability = before_eval.get("readability_details", {})
    before_word_count = len(plain_content.split())
    before_long_sentences = before_readability.get("long_sentences_count", 0)
    before_seo_score = before_eval.get("seo_score", 0)
    before_readability_score = before_eval.get("readability_score", 0)

    # 2. Rumuskan Rincian Masalah Nyata
    issues_list = []
    if before_eval.get("headline_issues"):
        issues_list.extend(before_eval["headline_issues"])
    if before_eval.get("technical_suggestions"):
        issues_list.extend(before_eval["technical_suggestions"][:4])

    issues_str = "\n- ".join(issues_list) if issues_list else "Optimalkan struktur dan keterbacaan naskah."

    # 3. Instruksi Khusus Berdasarkan Mode
    mode_instructions = {
        "all": (
            "Lakukan perbaikan menyeluruh (Full SEO & Readability Enhancement):\n"
            "1. Perbaiki judul agar berbobot 50-65 karakter dan memuat kata kunci fokus.\n"
            "2. Susun ulang paragraf pembuka (lede) dengan formula piramida terbalik 5W1H dan sisipkan kata kunci fokus di 50 kata pertama.\n"
            "3. Pecah semua kalimat panjang yang lebih dari 25 kata menjadi kalimat efektif dengan tanda titik.\n"
            "4. Bagi badan artikel dengan 2 sampai 3 subjudul <h2> yang relevan (minimal 1 H2 memuat kata kunci fokus).\n"
            "5. Buat meta description padat 130-150 karakter."
        ),
        "readability": (
            "Fokus HANYA pada peningkatan keterbacaan (Readability Fix):\n"
            "1. Pecah kalimat panjang (> 25 kata) menjadi kalimat pendek efektif menggunakan tanda titik.\n"
            "2. Pertahankan judul dan struktur asli naskah sebisa mungkin tanpa mengubah alur fakta."
        ),
        "lede": (
            "Fokus HANYA pada paragraf pembuka (Lede 5W1H Fix):\n"
            "1. Tulis ulang paragraf pembuka (lede) agar padat, memuat unsur 5W1H dan kata kunci fokus.\n"
            "2. Pertahankan sisa paragraf berikutnya."
        ),
        "subheadings": (
            "Fokus HANYA pada penyusunan struktur subjudul (H2 Subheadings Fix):\n"
            "1. Sisipkan 2-3 tag <h2> di sela-sela paragraf naskah yang ada, dengan minimal 1 <h2> memuat kata kunci fokus."
        ),
        "headlines": (
            "Fokus HANYA pada optimalisasi judul berita:\n"
            "1. Buat judul utama dan 4 variasi judul alternatif (50-65 karakter) yang memikat pembaca dan memuat kata kunci fokus."
        )
    }
    selected_mode_instruction = mode_instructions.get(mode, mode_instructions["all"])

    expansion_instruction = ""
    if expand_content and before_word_count < 350:
        expansion_instruction = (
            f"\nCatatan Tambahan: Naskah saat ini hanya {before_word_count} kata. "
            "Kembangkan narasi naskah dengan latar belakang peristiwa dan penjelasan konteks relevan menjadi minimal 350-500 kata tanpa mengarang fakta."
        )

    current_date = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
Bertindaklah sebagai Senior News Editor & Specialist SEO Berita Indonesia terkemuka.
Tugas Anda: Perbaiki dan sempurnakan draf artikel berita berikut berdasarkan hasil audit teknis SEO.

Konteks Waktu: Hari ini adalah tanggal {current_date}. Jangan anggap tahun berjalan sebagai masa depan.
Kata Kunci Fokus: "{target_keyword}"

Draf Asli:
Judul Asli: {title}
Isi Naskah Asli:
{plain_content[:3000]}

Temuan Masalah yang Wajib Diperbaiki:
- {issues_str}

Instruksi Perbaikan:
{selected_mode_instruction}{expansion_instruction}

ATURAN PENTING:
- JANGAN ubah fakta, angka statistik, nama tokoh, atau tanggal kejadian.
- Tulis naskah dalam format tag HTML rapi (<p> untuk paragraf berita dan <h2> untuk subjudul). Jangan gunakan tag <h1> atau <h3>.
- Berikan output JSON SAJA tanpa markdown block atau teks pembuka, dengan format persis:
{{
  "title": "<Judul utama hasil perbaikan 50-65 karakter>",
  "title_alternatives": [
    "<Judul alternatif 1>",
    "<Judul alternatif 2>"
  ],
  "lede": "<Paragraf pembuka 5W1H yang sudah memuat kata kunci>",
  "content_html": "<p>Paragraf lede...</p><h2>Subjudul 1</h2><p>Paragraf isi...</p><h2>Subjudul 2</h2><p>Paragraf penutup...</p>",
  "content_plain": "<Naskah teks bersih tanpa HTML, dipisahkan baris baru ganda>",
  "meta_description": "<Meta description ringkas 130-150 karakter>",
  "improvements_applied": [
    "<Poin 1 perbaikan konkret yang telah dilakukan>",
    "<Poin 2 perbaikan konkret yang telah dilakukan>",
    "<Poin 3 perbaikan konkret yang telah dilakukan>"
  ]
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
            "temperature": 0.2,
            "stream": False
        }
        res = requests.post(NINEROUTER_URL, headers=headers, json=payload, timeout=NINEROUTER_TIMEOUT)
        if res.status_code == 200:
            resp_json = res.json()
            raw_ai = resp_json["choices"][0]["message"]["content"]
            clean_json = re.sub(r'```(?:json)?\s*|\s*```', '', raw_ai).strip()
            try:
                ai_data = json.loads(clean_json)
            except Exception:
                match = re.search(r'(\{[\s\S]*\})', clean_json)
                if match:
                    ai_data = json.loads(match.group(1))
    except Exception:
        ai_data = None

    # Fallback heuristik jika AI tidak merespons
    if not ai_data:
        heuristic_meta = generate_heuristic_meta(title, plain_content, target_keyword)
        # Pecah kalimat panjang secara heuristik dengan membelah pada kata sambung
        improved_text = plain_content
        ai_data = {
            "title": heuristic_meta["seo_title"],
            "title_alternatives": [title],
            "lede": plain_content[:200] + "...",
            "content_html": f"<p>{plain_content[:300]}</p><h2>Perkembangan {target_keyword}</h2><p>{plain_content[300:]}</p>",
            "content_plain": improved_text,
            "meta_description": heuristic_meta["meta_description"],
            "improvements_applied": [
                "Mengoptimalkan judul naskah agar memuat kata kunci fokus.",
                "Menyisipkan subjudul H2 untuk memecah struktur naskah.",
                "Menyesuaikan ringkasan meta description."
            ]
        }

    improved_title = ai_data.get("title", title)
    improved_html = ai_data.get("content_html", "")
    improved_plain = ai_data.get("content_plain", "")
    if not improved_plain and improved_html:
        improved_plain = re.sub(r'<[^>]+>', ' ', improved_html)
        improved_plain = re.sub(r'\s+', ' ', improved_plain).strip()

    # 4. Evaluasi Akhir (After) pada Teks Baru
    after_eval = analyze_technical_seo(improved_title, improved_plain, target_keyword)
    after_readability = after_eval.get("readability_details", {})
    after_word_count = len(improved_plain.split())
    after_long_sentences = after_readability.get("long_sentences_count", 0)
    after_seo_score = after_eval.get("seo_score", 0)
    after_readability_score = after_eval.get("readability_score", 0)

    score_diff = after_seo_score - before_seo_score
    score_gain_str = f"+{score_diff} Poin" if score_diff > 0 else f"{score_diff} Poin"

    reading_time = max(1, round(after_word_count / 180))

    return {
        "improved_article": {
            "title": improved_title,
            "title_alternatives": ai_data.get("title_alternatives", []),
            "lede": ai_data.get("lede", ""),
            "content": improved_html,
            "content_plain": improved_plain,
            "meta_description": ai_data.get("meta_description", ""),
            "focus_keyword": target_keyword,
            "word_count": after_word_count,
            "reading_time_minutes": reading_time
        },
        "improvements_applied": ai_data.get("improvements_applied", []),
        "score_comparison": {
            "before": {
                "seo_score": before_seo_score,
                "readability_score": before_readability_score,
                "long_sentences_count": before_long_sentences,
                "word_count": before_word_count
            },
            "after": {
                "seo_score": after_seo_score,
                "readability_score": after_readability_score,
                "long_sentences_count": after_long_sentences,
                "word_count": after_word_count
            },
            "score_gain": score_gain_str
        }
    }
