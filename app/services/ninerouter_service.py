import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv

load_dotenv()

# Konfigurasi 9Router AI Proxy Gateway (baca dari .env)
NINEROUTER_URL = os.getenv("NINEROUTER_URL", "https://api.ninerouter.com/v1/chat/completions")
NINEROUTER_API_KEY = os.getenv("NINEROUTER_API_KEY", "")


def call_9router_for_geo(
    title: str,
    content: str,
    keyword: str = "",
    category: str = "",
    meta_keywords: Optional[list] = None
) -> Dict[str, Any]:
    """Panggil 9Router AI Proxy untuk evaluasi kualitatif GEO & E-E-A-T serta auto-generate SEO metadata."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    keyword_text = keyword.strip() if keyword else ""
    meta_hint = f"Kata Kunci Meta Terdeteksi dari Halaman/Kompetitor: {', '.join(meta_keywords[:6])}\n" if meta_keywords else ""

    keyword_instruction = f"Kata Kunci Fokus yang dimasukkan penulis: \"{keyword_text}\"" if keyword_text else (
        "Kata Kunci Fokus: (KOSONG)\n"
        f"{meta_hint}"
        "Instruksi Khusus Kata Kunci:\n"
        "- 'detected_competitor_keyword': Analisis judul, meta keywords, dan isi berita di atas, lalu tentukan kata kunci utama yang kemungkinan besar dibidik/dipakai oleh kompetitor/penulis artikel ini.\n"
        "- 'focus_keyword': Tentukan 1 rekomendasi kata kunci fokus terbaik (2-4 kata) yang memiliki potensi pencarian tinggi di Google jika redaksi ingin menulis artikel serupa atau mengoptimasi halaman web sendiri.\n"
        "- 'keyword_variations': Berikan 2-4 variasi kata kunci turunan yang relevan untuk memperkaya artikel."
    )
    category_instruction = f"Kategori/Rubrik Berita: \"{category.strip()}\"\n" if category and category.strip() else ""

    prompt = f"""
Bertindaklah sebagai Senior SEO Engine Evaluator & Editor Berita Indonesia.
Konteks Waktu: Hari ini adalah tanggal {current_date}. Jangan anggap tahun berjalan sebagai masa depan.
Evaluasi artikel berikut berdasarkan standar GEO (Generative Engine Optimization), E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness), dan praktik terbaik SEO Google.

Judul: {title}
{category_instruction}{keyword_instruction}
Konten: {content}

ATURAN PENTING PENULISAN SARAN:
1. Berikan saran yang KONKRET, DETAIL, dan LENGKAP DENGAN CONTOH SOLUSI (Actionable Suggestions). JANGAN hanya menulis kritik kering atau kalimat pendek/terpotong-potong gaya telegraf/robotik.
2. Setiap poin saran wajib menyertakan tindakan nyata beserta contoh kalimat/narasumber/data yang dapat langsung diterapkan:
   - Experience: Jelaskan siapa yang perlu diwawancarai dan berikan contoh kutipannya (contoh: "Tambahkan wawancara peserta di lapangan untuk membuktikan dampak nyata, misal: 'Saya sangat terbantu dengan program ini untuk mengasah keterampilan praktis,' ungkap salah seorang peserta.").
   - Expertise: Sebutkan bidang kepakaran atau data rujukan konkret yang perlu ditambahkan (contoh: "Kutip pandangan pengamat teknologi atau data riset untuk memvalidasi klaim efisiensi.").
   - Authoritativeness: Sebutkan nama lembaga/instansi resmi atau tautan dokumen acuan yang relevan untuk ditautkan.
   - Trustworthiness: Berikan saran cara menyeimbangkan perspektif berita (misal jika berita bersumber dari rilis pers sepihak, sarankan konfirmasi ke pihak pengamat independen atau masyarakat).
3. Untuk "seo_title": Buat 1 judul alternatif terbaik (50-65 karakter) yang memuat kata kunci fokus dan menarik pembaca berita (contoh: "Kemnaker Dorong Generasi Muda Kuasai AI untuk Tingkatkan Produktivitas Kerja").
4. Untuk "editor_notes": Buat paragraf ulasan redaksional yang mengalir profesional, ramah, dan membimbing penulis langkah demi langkah.

Berikan output JSON SAJA tanpa penjelasan tambahan, dengan struktur format persis:
{{
  "detected_competitor_keyword": "<Kata kunci yang terdeteksi dipakai/dibidik oleh kompetitor pada artikel ini, atau kosong jika URL sendiri>",
  "focus_keyword": "<1 frasa kunci fokus terbaik 2-4 kata untuk SEO jika menulis artikel ini>",
  "keyword_variations": ["<variasi keyword 1>", "<variasi keyword 2>", "<variasi keyword 3>"],
  "seo_title": "<Judul SEO optimal 50-60 karakter yang menarik klik dan mengandung focus_keyword>",
  "meta_description": "<Meta description ringkas, padat, 130-150 karakter yang memancing klik dan merangkum inti berita>",
  "eeat_score": <angka 1-100>,
  "experience": {{
      "score": <angka 1-100>,
      "has_firsthand_experience": <true/false>,
      "suggestions": ["<Saran konkret beserta contoh nyata perbaikan>"]
  }},
  "expertise": {{
      "score": <angka 1-100>,
      "has_expert_sources": <true/false>,
      "has_data_statistics": <true/false>,
      "suggestions": ["<Saran konkret beserta contoh nyata perbaikan>"]
  }},
  "authoritativeness": {{
      "score": <angka 1-100>,
      "has_official_sources": <true/false>,
      "has_citations": <true/false>,
      "suggestions": ["<Saran konkret beserta contoh nyata perbaikan>"]
  }},
  "trustworthiness": {{
      "score": <angka 1-100>,
      "is_balanced": <true/false>,
      "has_verification": <true/false>,
      "suggestions": ["<Saran konkret beserta contoh nyata perbaikan>"]
  }},
  "editor_notes": "<Paragraf catatan editor yang mengalir profesional merangkum prioritas perbaikan beserta rekomendasi judul dan angle berita>"
}}
"""
    try:
        headers = {
            "Authorization": f"Bearer {NINEROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "ag/gemini-pro-agent",  # 9Router akan mengarahkan ke LLM aktif
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "stream": False
        }
        res = requests.post(NINEROUTER_URL, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            try:
                resp_json = res.json()
                ai_data = resp_json["choices"][0]["message"]["content"]
            except Exception:
                raise Exception(f"Response bukan JSON format OpenAI. Teks: {res.text[:200]}")

            # Extract JSON response from AI
            clean_json = re.sub(r'```json\s*|\s*```', '', ai_data).strip()
            return json.loads(clean_json)
        else:
            raise Exception(f"HTTP {res.status_code}: {res.text[:200]}")
    except Exception as e:
        return {
            "detected_competitor_keyword": meta_keywords[0] if meta_keywords else "",
            "focus_keyword": keyword.strip() if keyword else "",
            "keyword_variations": meta_keywords[1:4] if meta_keywords and len(meta_keywords) > 1 else [],
            "seo_title": title[:60] if title else "",
            "meta_description": "",
            "eeat_score": 0,
            "experience": { "score": 0, "has_firsthand_experience": False, "suggestions": [] },
            "expertise": { "score": 0, "has_expert_sources": False, "has_data_statistics": False, "suggestions": [] },
            "authoritativeness": { "score": 0, "has_official_sources": False, "has_citations": False, "suggestions": [] },
            "trustworthiness": { "score": 0, "is_balanced": False, "has_verification": False, "suggestions": [f"Gagal menghubungkan ke 9Router AI: {str(e)}"] },
            "editor_notes": "Analisis AI gagal. Terapkan standar penulisan berita konvensional (Cek tanggal, 5W1H, panjang judul)."
        }


def call_9router_for_taxonomy(name: str, description: str = "", taxonomy_type: str = "category") -> Dict[str, Any]:
    """Panggil 9Router AI Proxy untuk evaluasi taksonomi berita (kategori, tag, topik)."""
    type_label = "Tag/Entitas Berita" if taxonomy_type in ("post_tag", "tag") else (
        "Topik Khusus/Tren" if taxonomy_type in ("newstopic", "topic") else "Kategori Berita"
    )
    desc_text = description.strip() if description else "Belum ada deskripsi"

    prompt = f"""
Bertindaklah sebagai Senior SEO Engine Specialist untuk portal berita Indonesia.
Evaluasi halaman arsip taksonomi berita berikut:

Tipe Taksonomi: {type_label}
Nama: {name}
Deskripsi Saat Ini: {desc_text}

Tugas:
1. Buat "seo_title" halaman arsip berita (50-60 karakter) yang menarik pembaca dan ramah mesin pencari (contoh: "Berita {name} Terkini & Update Populer | BorneoFlash").
2. Buat "meta_description" halaman arsip (120-155 karakter) yang memicu klik pencarian Google dan menjelaskan topik {name}.
3. Tentukan "focus_keyword" paling relevan untuk pencarian Google terkait topik ini (contoh: "berita {name.lower()}").
4. Buat "improved_description" berupa narasi pengantar arsip yang kaya informasi, natural, dan kontekstual (minimal 100-200 karakter) untuk membantu pembaca memahami topik ini.
5. Berikan "seo_score" (1-100) dan "readability_score" (1-100) berdasarkan kualitas nama dan deskripsi.
6. Berikan 3 poin "suggestions" konkret untuk optimasi halaman arsip taksonomi ini.

Berikan output JSON SAJA tanpa penjelasan tambahan, dengan format persis:
{{
  "seo_title": "<Judul SEO 50-60 karakter>",
  "meta_description": "<Meta description 120-155 karakter>",
  "focus_keyword": "<Frasa kunci target>",
  "seo_score": <angka 1-100>,
  "readability_score": <angka 1-100>,
  "suggestions": [
    "<Saran konkret 1>",
    "<Saran konkret 2>",
    "<Saran konkret 3>"
  ],
  "improved_description": "<Deskripsi arsip yang informatif dan kaya kata kunci>"
}}
"""
    try:
        headers = {
            "Authorization": f"Bearer {NINEROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "ag/gemini-pro-agent",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "stream": False
        }
        res = requests.post(NINEROUTER_URL, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            try:
                resp_json = res.json()
                ai_data = resp_json["choices"][0]["message"]["content"]
            except Exception:
                raise Exception(f"Response bukan format OpenAI JSON. Teks: {res.text[:200]}")

            clean_json = re.sub(r'```json\s*|\s*```', '', ai_data).strip()
            return json.loads(clean_json)
        else:
            raise Exception(f"HTTP {res.status_code}: {res.text[:200]}")
    except Exception:
        return {}
