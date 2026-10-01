import re
from typing import Dict, Any, List, Set, Tuple

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Inisialisasi Stemmer PySastrawi (singleton)
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Stopwords bahasa Indonesia untuk ekstraksi & pencocokan keyword
STOPWORDS_ID: Set[str] = {
    "di", "ke", "dari", "dan", "atau", "yang", "untuk", "dengan", "pada", "dalam",
    "oleh", "ini", "itu", "se", "ter", "guna", "agar", "karena", "sebab", "maka",
    "lalu", "kemudian", "serta", "juga", "bagi", "tentang", "adalah", "merupakan",
    "bisa", "dapat", "akan", "telah", "sudah", "sedang", "bukan", "tidak", "belum"
}

# Singkatan dan gelar umum bahasa Indonesia untuk proteksi pemecah kalimat
ABBREVIATIONS_ID: List[str] = [
    r'dr\.', r'ir\.', r'h\.', r'hj\.', r'drs\.', r'dra\.', r'prof\.', r'k\.h\.',
    r'no\.', r'hlm\.', r'dsb\.', r'dll\.', r'dst\.', r'sbb\.', r'yaitu\.',
    r's\.e\.', r'm\.e\.', r's\.kom\.', r'm\.kom\.', r's\.pd\.', r'm\.pd\.',
    r's\.h\.', r'm\.h\.', r's\.sos\.', r'm\.si\.', r's\.t\.', r'm\.t\.'
]


def clean_text(text: str) -> str:
    """Membersihkan tag HTML dan karakter khusus, menghasilkan teks huruf kecil dengan spasi rapi."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'[^\w\s]', ' ', clean)
    return " ".join(clean.lower().split())


def split_sentences_id(text: str) -> List[str]:
    """Memecah teks menjadi daftar kalimat dengan memproteksi singkatan gelar, jam, dan angka desimal."""
    if not text:
        return []

    plain = re.sub(r'<[^>]+>', ' ', text)
    t = ' ' + plain.strip() + ' '

    for abb in ABBREVIATIONS_ID:
        t = re.sub(r'(?i)\b' + abb, lambda m: m.group(0).replace('.', '__DOT__'), t)

    t = re.sub(r'(\d+)\.(\d+)', r'\1__DOT__\2', t)

    raw_sentences = re.split(r'[\.\!\?]+[\s\n]+', t)
    sentences = []
    for s in raw_sentences:
        clean_s = s.replace('__DOT__', '.').strip()
        if len(clean_s.split()) >= 2:
            sentences.append(clean_s)
    return sentences


def split_paragraphs(content: str) -> List[str]:
    """Ekstraksi paragraf dari teks atau dokumen HTML."""
    if not content:
        return []
    if '<p' in content.lower():
        raw_paras = re.findall(r'<p[^>]*>(.*?)</p>', content, flags=re.DOTALL | re.IGNORECASE)
    else:
        raw_paras = re.split(r'\n\s*\n', content)

    paragraphs = []
    for p in raw_paras:
        clean_p = re.sub(r'<[^>]+>', ' ', p).strip()
        if len(clean_p.split()) >= 3:
            paragraphs.append(clean_p)

    return paragraphs or ([content.strip()] if content.strip() else [])


def extract_focus_keyword_heuristic(title: str, content: str = "") -> str:
    """Ekstraksi kata kunci fokus heuristik dari judul berita jika tidak ada AI."""
    if not title:
        return ""

    cleaned = re.sub(r'[\?!:;"\'\(\)\[\]\{\}]', '', title).strip()
    parts = re.split(r'\s*[-|,]\s*', cleaned)
    main_part = parts[0].strip() if parts else cleaned

    words = [w for w in main_part.split() if w.strip()]
    if not words:
        words = [w for w in cleaned.split() if w.strip()]

    while words and words[0].lower() in STOPWORDS_ID:
        words.pop(0)
    while words and words[-1].lower() in STOPWORDS_ID:
        words.pop()

    candidate = " ".join(words[:4]) if len(words) >= 4 else " ".join(words)
    return candidate.strip() or title[:30].strip()


def generate_heuristic_meta(title: str, content: str, keyword: str = "") -> Dict[str, str]:
    """Generate judul SEO dan meta description fallback lokal jika AI tidak aktif."""
    clean_c = clean_text(content)
    raw_sentences = [s.strip() for s in re.split(r'[\.\n]+', clean_c) if s.strip()]
    desc = ""
    for s in raw_sentences:
        if len(desc) + len(s) + 1 <= 155:
            desc = (desc + " " + s).strip()
        else:
            break
    if not desc and raw_sentences:
        desc = raw_sentences[0][:155]
    if not desc:
        desc = (title + " - Baca berita dan ulasan selengkapnya di BorneoFlash.")[:155]

    seo_title = title.strip()
    if len(seo_title) > 60:
        seo_title = seo_title[:57] + "..."

    return {
        "focus_keyword": keyword or extract_focus_keyword_heuristic(title, content),
        "seo_title": seo_title,
        "meta_description": desc
    }


def analyze_lede_5w1h(lede_text: str) -> Dict[str, Any]:
    """Analisis elemen jurnalistik 5W+1H pada lede (paragraf pembuka berita)."""
    t_lower = lede_text.lower()

    # 1. Kapan (When)
    days = {'senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu'}
    months = {'januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'}
    rel_time = {'kemarin', 'tadi malam', 'pagi ini', 'siang ini', 'sore ini', 'malam ini', 'pekan lalu', 'minggu lalu', 'hari ini', 'wita', 'wib', 'wit'}
    has_date_num = bool(re.search(r'\b\d{1,2}[\/\-\s]+(\d{1,2}|januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember|\d{4})\b', t_lower))
    has_day = any(d in t_lower for d in days)
    has_month = any(m in t_lower for m in months)
    has_rel_time = any(r in t_lower for r in rel_time)
    has_when = has_date_num or has_day or has_month or has_rel_time

    # 2. Di mana (Where)
    locations = {
        'balikpapan', 'samarinda', 'kaltim', 'kalimantan timur', 'kalimantan', 'penajam', 'paser',
        'kutai kartanegara', 'kukar', 'kutai barat', 'kubar', 'kutai timur', 'kutim', 'berau',
        'bontang', 'mahakam ulu', 'mahakam', 'ikn', 'nusantara', 'ibu kota nusantara', 'jakarta',
        'indonesia', 'kantor', 'gedung', 'jalan', 'lapangan', 'wilayah', 'daerah'
    }
    has_dateline = bool(re.search(r'^[a-z\s]+[\s\-–—]+\b', t_lower))
    has_where = any(loc in t_lower for loc in locations) or has_dateline

    # 3. Siapa (Who)
    actors = {
        'presiden', 'wapres', 'menteri', 'kementerian', 'kemnaker', 'gubernur', 'walikota', 'wali kota',
        'bupati', 'kapolda', 'kapolres', 'dirlantas', 'direskrim', 'polisi', 'polri', 'tni', 'kejati',
        'kejari', 'hakim', 'jaksa', 'dinas', 'kepala dinas', 'kadis', 'kepala', 'ketua', 'direktur',
        'manager', 'pejabat', 'petugas', 'warga', 'masyarakat', 'generasi muda', 'korban', 'tersangka',
        'pelaku', 'saksi', 'peserta', 'pemprov', 'pemkot', 'pemkab', 'dprd', 'kpu', 'bawaslu'
    }
    has_who = any(act in t_lower for act in actors)

    # 4. Apa / Tindakan (What / Action)
    actions = {
        'mendorong', 'menggelar', 'gelar', 'resmikan', 'meresmikan', 'tangkap', 'menangkap', 'amankan',
        'mengamankan', 'sosialisasi', 'peringatkan', 'imbau', 'mengimbau', 'luncurkan', 'meluncurkan',
        'bahas', 'tinjau', 'meninjau', 'laksanakan', 'rapat', 'sidang', 'kebakaran', 'kecelakaan',
        'tabrakan', 'banjir', 'kasus', 'program', 'kegiatan', 'terjadi', 'meningkat', 'dorong'
    }
    has_what = any(act in t_lower for act in actions)

    # 5. Bagaimana / Atribusi Sumber (How / Attribution)
    quotes = {
        'ujar', 'kata', 'tutur', 'jelas', 'jelasnya', 'tandas', 'tegas', 'tegasnya', 'pungkas',
        'imbuh', 'beber', 'terang', 'terangnya', 'ungkap', 'menurut', 'berdasarkan', 'menyampaikan'
    }
    has_how = any(q in t_lower for q in quotes)

    elements_count = sum([has_when, has_where, has_who, has_what, has_how])
    return {
        "when": has_when,
        "where": has_where,
        "who": has_who,
        "what": has_what,
        "how": has_how,
        "elements_count": elements_count,
        "is_complete": elements_count >= 3
    }


def analyze_readability(sentences: List[str], paragraphs: List[str], total_words: int) -> Tuple[int, Dict[str, Any], List[str]]:
    """Analisis keterbacaan berita: ASL, deteksi kalimat panjang, dan panjang paragraf."""
    total_sentences = max(len(sentences), 1)
    total_paras = max(len(paragraphs), 1)
    asl = round(total_words / total_sentences, 1)
    avg_para_words = round(total_words / total_paras, 1)

    long_sentences = [s for s in sentences if len(s.split()) > 25]
    long_sentence_ratio = round((len(long_sentences) / total_sentences) * 100, 1)

    long_paragraphs = [p for p in paragraphs if len(clean_text(p).split()) > 80]

    score = 100
    suggestions = []

    # Penalti ASL (Ideal: 12-18 kata)
    if 10 <= asl <= 18:
        pass
    elif 19 <= asl <= 22:
        score -= 8
    elif 23 <= asl <= 26:
        score -= 16
        suggestions.append(f"Rata-rata panjang kalimat {asl} kata/kalimat (cukup panjang). Target ideal: 12-18 kata per kalimat.")
    elif asl > 26:
        score -= 25
        suggestions.append(f"Rata-rata kalimat terlalu panjang ({asl} kata/kalimat). Sederhanakan susunan kalimat majemuk menjadi kalimat-kalimat tunggal yang lincah.")
    elif asl < 8:
        score -= 5

    # Penalti Kalimat Panjang (> 25 kata)
    if len(long_sentences) > 0:
        if long_sentence_ratio > 30:
            score -= 15
        else:
            score -= 8

        first_sample = long_sentences[0]
        sample_words = first_sample.split()
        sample_preview = " ".join(sample_words[:7]) + "..." if len(sample_words) > 7 else first_sample
        suggestions.append(f"Terdapat {len(long_sentences)} kalimat dengan lebih dari 25 kata (contoh: \"{sample_preview}\"). Pecah kalimat panjang tersebut dengan tanda titik.")

    # Penalti Paragraf Terlalu Panjang
    if len(long_paragraphs) > 0:
        score -= 10
        suggestions.append(f"Terdapat {len(long_paragraphs)} paragraf yang terlalu panjang (>80 kata). Pecah menjadi 1-3 kalimat per paragraf agar nyaman dibaca di layar smartphone.")

    # Penalti Artikel Terlalu Pendek
    if total_words < 250:
        score -= 15
        suggestions.append(f"Naskah artikel ({total_words} kata) masih terlalu pendek. Kembangkan naskah hingga minimal 300 kata untuk ulasan yang berbobot.")
    elif total_words < 300:
        score -= 5

    final_readability = max(0, min(100, score))

    details = {
        "asl": asl,
        "total_sentences": total_sentences,
        "total_paragraphs": total_paras,
        "avg_paragraph_words": avg_para_words,
        "long_sentences_count": len(long_sentences),
        "long_sentences_ratio": long_sentence_ratio,
        "long_paragraphs_count": len(long_paragraphs)
    }

    return final_readability, details, suggestions


def analyze_technical_seo(title: str, content: str, keyword: str = "") -> Dict[str, Any]:
    """Analisis teknis lokal menggunakan PySastrawi, Regex Cerdas, dan Aturan Heuristik Jurnalistik."""
    if not keyword or not keyword.strip():
        keyword = extract_focus_keyword_heuristic(title, content)

    cleaned_content = clean_text(content)
    cleaned_title = clean_text(title)
    cleaned_keyword = clean_text(keyword)

    words = cleaned_content.split()
    total_words = len(words)

    if total_words == 0:
        return {"error": "Konten terlalu pendek atau kosong."}

    sentences = split_sentences_id(content)
    paragraphs = split_paragraphs(content)

    # 1. Analisis Keyword (Exact, Stemmed, Coverage, & Adaptive Density)
    kw_words = [w for w in cleaned_keyword.split() if w]
    meaningful_kw = [w for w in kw_words if w not in STOPWORDS_ID]
    if not meaningful_kw:
        meaningful_kw = kw_words
    num_kw = len(meaningful_kw)

    # Exact phrase count
    exact_pattern = r'\b' + r'\s+'.join(re.escape(w) for w in kw_words) + r'\b'
    exact_count = len(re.findall(exact_pattern, cleaned_content))

    # Stemmed phrase count via PySastrawi
    stemmed_kw_words = [stemmer.stem(w) for w in kw_words]
    stemmed_content = stemmer.stem(cleaned_content)
    stemmed_pattern = r'\b' + r'\s+'.join(re.escape(w) for w in stemmed_kw_words) + r'\b'
    stemmed_count = len(re.findall(stemmed_pattern, stemmed_content))

    keyword_count = max(exact_count, stemmed_count)
    density = round((keyword_count / total_words) * 100, 2)

    # Keyword Coverage (sebaran kata kunci di dalam artikel)
    words_set = set(words)
    stemmed_words_set = set(stemmed_content.split())
    found_kw_words = []
    for i, w in enumerate(meaningful_kw):
        st = stemmed_kw_words[i] if i < len(stemmed_kw_words) else stemmer.stem(w)
        if w in words_set or st in stemmed_words_set:
            found_kw_words.append(w)
    missing_kw_words = [w for w in meaningful_kw if w not in found_kw_words]
    coverage = round((len(found_kw_words) / len(meaningful_kw)) * 100, 1) if meaningful_kw else 100.0

    # Target rentang density adaptif berdasarkan panjang kata kunci
    if num_kw == 1:
        min_dens, max_dens = 0.8, 3.0
        ideal_str = "1.0% - 2.5%"
        ideal_count_str = "sisipkan di 2-4 paragraf"
    elif num_kw == 2:
        min_dens, max_dens = 0.5, 2.2
        ideal_str = "0.6% - 1.8%"
        ideal_count_str = "sisipkan di 2-3 paragraf"
    else:
        min_dens, max_dens = 0.25, 1.5
        ideal_str = "0.3% - 1.0%"
        ideal_count_str = "cukup 1-3 kali penyebutan frasa utuh"

    score = 100
    suggestions = []

    # Penilaian status density
    if keyword_count == 0:
        if coverage == 100.0 and num_kw >= 3:
            score -= 8
            density_status = "Cukup (Sebaran kata lengkap, frasa utuh belum muncul)"
            suggestions.append(f"Semua kata kunci ('{', '.join(meaningful_kw)}') sudah ada di naskah (sebaran 100%), namun frasa utuh '{keyword}' belum tertulis berurutan. Sisipkan minimal 1 kali frasa lengkap '{keyword}' di judul atau lede pembuka.")
        else:
            score -= 15
            density_status = "Terlalu rendah"
            suggestions.append(f"Kata kunci fokus '{keyword}' belum tertulis di dalam naskah berita (0 kali / 0.0%). Sisipkan frasa '{keyword}' di paragraf pembuka (lead) dan minimal 1 paragraf isi.")
            if missing_kw_words:
                suggestions.append(f"Kata pembentuk keyword yang belum muncul di artikel: '{', '.join(missing_kw_words)}'.")
    elif (min_dens <= density <= max_dens) or (num_kw >= 3 and 1 <= keyword_count <= 4):
        density_status = "Ideal"
    elif density < min_dens:
        score -= 10
        density_status = "Terlalu rendah"
        suggestions.append(f"Kerapatan kata kunci '{keyword}' masih rendah ({density}%, muncul {keyword_count}x). Target ideal untuk {num_kw} kata: {ideal_str} ({ideal_count_str}).")
    else:
        score -= 20
        density_status = "Terlalu tinggi"
        suggestions.append(f"Terlalu banyak pengulangan kata kunci '{keyword}' / Keyword Stuffing ({density}%, muncul {keyword_count}x). Kurangi penyebutan agar lebih natural.")

    # 2. Cek Judul & Penempatan Keyword
    title_len = len(title)
    title_words = set(cleaned_title.split())
    keyword_in_title = all(w in title_words for w in meaningful_kw) if meaningful_kw else False

    if title_len < 40 or title_len > 70:
        score -= 10
        suggestions.append(f"Panjang judul saat ini {title_len} karakter. Idealnya antara 50-65 karakter.")

    if not keyword_in_title:
        score -= 15
        suggestions.append(f"Kata kunci fokus '{keyword}' tidak ditemukan di dalam judul.")

    # 3. Lede Analysis (Paragraf Pertama & 5W+1H)
    lede_text = paragraphs[0] if paragraphs else " ".join(words[:50])
    lede_analysis = analyze_lede_5w1h(lede_text)
    has_5w1h = lede_analysis["is_complete"]
    lede_quality = "Good" if has_5w1h else "Needs Improvement"

    lede_words_set = set(clean_text(lede_text).split())
    keyword_in_lede = all(w in lede_words_set for w in meaningful_kw) if meaningful_kw else False

    if not has_5w1h:
        score -= 10
        missing_lede_elements = []
        if not lede_analysis["when"]:
            missing_lede_elements.append("waktu kejadian (kapan)")
        if not lede_analysis["where"]:
            missing_lede_elements.append("lokasi (di mana)")
        if not lede_analysis["who"]:
            missing_lede_elements.append("aktor/lembaga (siapa)")
        if not lede_analysis["what"]:
            missing_lede_elements.append("tindakan/peristiwa (apa)")
        if missing_lede_elements:
            suggestions.append(f"Paragraf pembuka (lede) belum memuat unsur: {', '.join(missing_lede_elements)}. Terapkan formula piramida terbalik berita.")

    if not keyword_in_lede:
        score -= 10
        suggestions.append(f"Kata kunci fokus belum ada di paragraf pembuka (lede). Sisipkan kata kunci di 50 kata pertama agar mesin pencari memprioritaskan artikel.")

    # 4. Readability Analysis
    readability_score, readability_details, readability_suggestions = analyze_readability(sentences, paragraphs, total_words)
    suggestions.extend(readability_suggestions)

    # 5. Headline Issues & Candidate
    headline_issues = [s for s in suggestions if "judul" in s.lower()]
    candidate_title = title.strip()
    if len(candidate_title) > 65:
        candidate_title = candidate_title[:62] + "..."

    return {
        "seo_score": max(score, 0),
        "readability_score": readability_score,
        "headline_score": 100 if (40 <= title_len <= 70 and keyword_in_title) else (70 if keyword_in_title else 40),
        "headline_issues": headline_issues,
        "headline_suggestion": f"Gunakan judul alternatif: \"{candidate_title}\"" if headline_issues else "",
        "lede_quality": lede_quality,
        "lede_word_count": len(clean_text(lede_text).split()),
        "lede_has_5w1h": has_5w1h,
        "lede_has_keyword": keyword_in_lede,
        "keyword_density": density,
        "keyword_density_status": density_status,
        "keyword_coverage": coverage,
        "keyword_count": keyword_count,
        "readability_details": readability_details,
        "technical_suggestions": suggestions
    }
