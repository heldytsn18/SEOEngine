import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Konfigurasi 9Router AI Proxy Gateway (baca dari .env)
NINEROUTER_URL = os.getenv("NINEROUTER_URL", "https://api.ninerouter.com/v1/chat/completions")
NINEROUTER_API_KEY = os.getenv("NINEROUTER_API_KEY", "")


def call_9router_for_geo(title: str, content: str, keyword: str = "") -> Dict[str, Any]:
    """Panggil 9Router AI Proxy untuk evaluasi kualitatif GEO & E-E-A-T serta auto-generate SEO metadata."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    keyword_text = keyword.strip() if keyword else ""
    keyword_instruction = f"Kata Kunci Fokus yang dimasukkan penulis: \"{keyword_text}\"" if keyword_text else (
        "Kata Kunci Fokus: (KOSONG - Anda WAJIB menganalisis judul dan konten, lalu menentukan 1 kata kunci/frasa fokus terbaik (2-4 kata) yang memiliki potensi pencarian tinggi di Google)."
    )

    prompt = f"""
Bertindaklah sebagai Senior SEO Engine Evaluator & Editor Berita Indonesia.
Konteks Waktu: Hari ini adalah tanggal {current_date}. Jangan anggap tahun berjalan sebagai masa depan.
Evaluasi artikel berikut berdasarkan standar GEO (Generative Engine Optimization), E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness), dan praktik terbaik SEO Google.

Judul: {title}
{keyword_instruction}
Konten: {content}

Berikan output JSON SAJA tanpa penjelasan tambahan, dengan struktur format persis:
{{
  "focus_keyword": "<1 frasa kunci fokus terbaik 2-4 kata, gunakan kata kunci penulis jika ada, atau tentukan yang paling relevan jika kosong>",
  "seo_title": "<Judul SEO optimal 50-60 karakter yang menarik klik dan mengandung focus_keyword>",
  "meta_description": "<Meta description ringkas, padat, 130-150 karakter yang memancing klik dan merangkum inti berita>",
  "eeat_score": <angka 1-100>,
  "experience": {{
      "score": <angka 1-100>,
      "has_firsthand_experience": <true/false>,
      "suggestions": ["<saran>"]
  }},
  "expertise": {{
      "score": <angka 1-100>,
      "has_expert_sources": <true/false>,
      "has_data_statistics": <true/false>,
      "suggestions": ["<saran>"]
  }},
  "authoritativeness": {{
      "score": <angka 1-100>,
      "has_official_sources": <true/false>,
      "has_citations": <true/false>,
      "suggestions": ["<saran>"]
  }},
  "trustworthiness": {{
      "score": <angka 1-100>,
      "is_balanced": <true/false>,
      "has_verification": <true/false>,
      "suggestions": ["<saran>"]
  }},
  "editor_notes": "<Paragraf kohesif berisi instruksi editor seperti cek tanggal, perpendek judul, tambahkan kutipan, dll>"
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
            "focus_keyword": keyword.strip() if keyword else "",
            "seo_title": title[:60] if title else "",
            "meta_description": "",
            "eeat_score": 0,
            "experience": { "score": 0, "has_firsthand_experience": False, "suggestions": [] },
            "expertise": { "score": 0, "has_expert_sources": False, "has_data_statistics": False, "suggestions": [] },
            "authoritativeness": { "score": 0, "has_official_sources": False, "has_citations": False, "suggestions": [] },
            "trustworthiness": { "score": 0, "is_balanced": False, "has_verification": False, "suggestions": [f"Gagal menghubungkan ke 9Router AI: {str(e)}"] },
            "editor_notes": "Analisis AI gagal. Terapkan standar penulisan berita konvensional (Cek tanggal, 5W1H, panjang judul)."
        }
