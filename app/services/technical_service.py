import re
from typing import Dict, Any

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Inisialisasi Stemmer PySastrawi (singleton)
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Stopwords bahasa Indonesia untuk pencocokan keyword
STOPWORDS_ID = {"di", "ke", "dari", "dan", "atau", "yang", "untuk", "dengan", "pada", "dalam", "oleh", "ini", "itu", "se", "ter"}


def clean_text(text: str) -> str:
    """Membersihkan tag HTML dan karakter khusus."""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'[^\w\s]', '', clean)
    return clean.lower().strip()


def analyze_technical_seo(title: str, content: str, keyword: str) -> Dict[str, Any]:
    """Analisis teknis lokal menggunakan PySastrawi dan Aturan Heuristik."""
    cleaned_content = clean_text(content)
    cleaned_title = clean_text(title)
    cleaned_keyword = clean_text(keyword)

    words = cleaned_content.split()
    total_words = len(words)

    if total_words == 0:
        return {"error": "Konten terlalu pendek atau kosong."}

    # 1. Keyword Density menggunakan Stemming PySastrawi
    stemmed_keyword = stemmer.stem(cleaned_keyword)
    stemmed_content = stemmer.stem(cleaned_content)

    keyword_count = len(re.findall(r'\b' + re.escape(stemmed_keyword) + r'\b', stemmed_content))
    density = round((keyword_count / total_words) * 100, 2)

    # 2. Cek Judul & Keyword Placement (abaikan stopword, urutan bebas)
    title_len = len(title)
    keyword_words = [w for w in cleaned_keyword.split() if w not in STOPWORDS_ID]
    title_words = set(cleaned_title.split())
    keyword_in_title = all(w in title_words for w in keyword_words) if keyword_words else False

    # 3. Cek struktur paragraf & 5W1H dasar
    five_w_one_h = ["apa", "siapa", "dimana", "kapan", "mengapa", "bagaimana", "balikpapan", "kaltim"]
    found_elements = [word for word in five_w_one_h if word in cleaned_content]

    # Hitung Skor Teknis
    score = 100
    suggestions = []

    if title_len < 40 or title_len > 70:
        score -= 10
        suggestions.append(f"Panjang judul saat ini {title_len} karakter. Idealnya antara 50-65 karakter.")

    if not keyword_in_title:
        score -= 15
        suggestions.append("Kata kunci fokus tidak ditemukan di dalam Judul.")

    if density < 0.8:
        score -= 10
        suggestions.append(f"Kerapatan kata kunci terlalu rendah ({density}%). Target ideal: 1% - 2.5%.")
    elif density > 3.0:
        score -= 20
        suggestions.append(f"Terlalu banyak kata kunci / Keyword Stuffing ({density}%). Kurangi penggunaan kata kunci fokus.")

    if total_words < 250:
        score -= 15
        suggestions.append(f"Jumlah kata ({total_words} kata) terlalu pendek untuk artikel berita. Minimal 300 kata.")

    # 4. Lede Analysis (50 kata pertama)
    lede_words = words[:50]
    keyword_in_lede = all(w in lede_words for w in keyword_words) if keyword_words else False

    return {
        "seo_score": max(score, 0),
        "readability_score": min(100, max(0, 100 - (20 if total_words < 300 else 0))),
        "headline_score": 100 if (40 <= title_len <= 70 and keyword_in_title) else (70 if keyword_in_title else 40),
        "headline_issues": [s for s in suggestions if "judul" in s.lower() or "judul" in s.lower()],
        "headline_suggestion": "Perbaiki judul agar mengandung kata kunci dan panjangnya 50-65 karakter." if not keyword_in_title or title_len < 40 or title_len > 70 else "",
        "lede_quality": "Bagus" if len(found_elements) >= 3 else "Perlu Perbaikan",
        "lede_word_count": min(total_words, 50),
        "lede_has_5w1h": len(found_elements) > 0,
        "lede_has_keyword": keyword_in_lede,
        "keyword_density": density,
        "keyword_density_status": "Ideal" if 1.0 <= density <= 2.5 else ("Terlalu rendah" if density < 1.0 else "Terlalu tinggi"),
        "technical_suggestions": suggestions
    }
