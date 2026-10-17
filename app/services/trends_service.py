import re
import json
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Namespace Google Trends RSS
HT_NS = {"ht": "https://trends.google.com/trending/rss"}


def fetch_daily_trends(geo: str = "ID") -> List[Dict[str, Any]]:
    """Mengambil daftar topik pencarian terhangat hari ini dari Google Trends RSS feed resmi.
    
    Endpoint: https://trends.google.com/trending/rss?geo={geo}
    """
    url = f"https://trends.google.com/trending/rss?geo={geo.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_content = response.read()

        root = ET.fromstring(xml_content)
        items = root.findall(".//item")
        results = []

        for item in items:
            title_el = item.find("title")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""

            approx_el = item.find("ht:approx_traffic", HT_NS)
            approx_traffic = approx_el.text.strip() if approx_el is not None and approx_el.text else ""

            pub_date_el = item.find("pubDate")
            pub_date = pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else ""

            desc_el = item.find("description")
            description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""

            picture_el = item.find("ht:picture", HT_NS)
            picture_url = picture_el.text.strip() if picture_el is not None and picture_el.text else ""

            # Berita terkait yang memicu tren
            news_title = ""
            news_snippet = ""
            news_url = ""
            news_source = ""

            news_item_el = item.find("ht:news_item", HT_NS)
            if news_item_el is not None:
                nt_el = news_item_el.find("ht:news_item_title", HT_NS)
                if nt_el is not None and nt_el.text:
                    news_title = nt_el.text.strip()

                ns_el = news_item_el.find("ht:news_item_snippet", HT_NS)
                if ns_el is not None and ns_el.text:
                    news_snippet = ns_el.text.strip()

                nu_el = news_item_el.find("ht:news_item_url", HT_NS)
                if nu_el is not None and nu_el.text:
                    news_url = nu_el.text.strip()

                nsrc_el = news_item_el.find("ht:news_item_source", HT_NS)
                if nsrc_el is not None and nsrc_el.text:
                    news_source = nsrc_el.text.strip()

            if title:
                results.append({
                    "title": title,
                    "approx_traffic": approx_traffic,
                    "pub_date": pub_date,
                    "description": description,
                    "news_title": news_title,
                    "news_snippet": news_snippet,
                    "news_url": news_url,
                    "news_source": news_source,
                    "picture_url": picture_url
                })

        return results
    except Exception as e:
        logger.warning(f"Gagal mengambil Google Trends RSS feed ({geo}): {str(e)}")
        return []


def _fetch_raw_autocomplete(query: str, geo: str = "ID", lang: str = "id") -> List[str]:
    """Helper internal untuk mengambil saran Google Suggest API mentah."""
    clean_q = query.strip()
    if not clean_q:
        return []

    encoded_q = urllib.parse.quote_plus(clean_q)
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={encoded_q}&hl={lang}&gl={geo}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if isinstance(payload, list) and len(payload) >= 2 and isinstance(payload[1], list):
            return [str(s).strip() for s in payload[1] if s and str(s).strip()]
        return []
    except Exception as e:
        logger.warning(f"Gagal mengambil Google Autocomplete untuk '{clean_q}': {str(e)}")
        return []


def fetch_google_autocomplete(query: str, geo: str = "ID", lang: str = "id") -> List[str]:
    """Mengambil saran kueri pencarian Google Autocomplete (Google Suggest API).
    
    Dilengkapi mekanisme dekomposisi kueri cerdas (Query Relaxation):
    Jika kueri terlalu spesifik/panjang dan Google Suggest tidak mengembalikan hasil exact match,
    sistem secara otomatis mengekstrak kata kunci inti dan mengumpulkan variasi pencarian Google
    yang relevan bagi redaktur berita.
    """
    clean_q = query.strip()
    if not clean_q:
        return []

    # 1. Coba kueri asli
    results = _fetch_raw_autocomplete(clean_q, geo=geo, lang=lang)
    if len(results) >= 4:
        return results[:8]

    # 2. Relaksasi kueri jika hasil minim/kosong
    stopwords = {
        "cegah", "sejak", "dini", "yang", "di", "ke", "dari", "untuk", "pada", "dan", "atau",
        "ini", "itu", "adalah", "dalam", "bisa", "akan", "sudah", "telah", "susun", "menggelar",
        "rapat", "bahwa", "oleh", "tentang", "agar", "supaya", "saat", "juga", "bagi", "komisi"
    }
    words = [re.sub(r"[^\w]", "", w.lower()) for w in clean_q.split() if len(w) > 2]
    meaningful = [w for w in words if w not in stopwords]

    candidates = []
    # Kombinasi pasangan kata berdampingan (bigram)
    if len(meaningful) >= 2:
        for i in range(len(meaningful) - 1):
            candidates.append(f"{meaningful[i]} {meaningful[i+1]}")
        # Kombinasi kata pertama dan kata terakhir
        if len(meaningful) >= 3:
            candidates.append(f"{meaningful[0]} {meaningful[-1]}")

    # Kombinasi kata tunggal signifikan
    for w in meaningful:
        if len(w) >= 4 and w not in candidates:
            candidates.append(w)

    for cand in candidates:
        sub_res = _fetch_raw_autocomplete(cand, geo=geo, lang=lang)
        for s in sub_res:
            if s not in results:
                results.append(s)
            if len(results) >= 8:
                break
        if len(results) >= 8:
            break

    return results[:8]


def fetch_people_also_ask(keyword: str, geo: str = "ID") -> List[str]:
    """Mengambil pertanyaan umum yang dicari publik di Google (People Also Ask) berbasis pola tanya 5W+1H Indonesia.
    
    Dilengkapi fallback otomatis ke formula kurasi jurnalistik jika data Google Suggest kueri minim.
    """
    clean_kw = keyword.strip()
    if not clean_kw:
        return []

    # Ekstrak kata kunci inti bila frasa kata kunci terlalu panjang
    stopwords = {
        "cegah", "sejak", "dini", "yang", "di", "ke", "dari", "untuk", "pada", "dan", "atau",
        "ini", "itu", "adalah", "dalam", "bisa", "akan", "sudah", "telah", "susun", "menggelar",
        "rapat", "bahwa", "oleh", "tentang", "agar", "supaya", "saat", "juga", "bagi", "komisi"
    }
    words = [re.sub(r"[^\w]", "", w.lower()) for w in clean_kw.split() if len(w) > 2]
    meaningful = [w for w in words if w not in stopwords]
    core_kw = " ".join(meaningful[:2]) if len(meaningful) >= 2 else (meaningful[0] if meaningful else clean_kw)

    question_prefixes = ["kenapa", "bagaimana", "kapan", "dimana", "apa itu", "syarat", "aturan", "berapa"]
    results = []

    for prefix in question_prefixes:
        query_pattern = f"{prefix} {core_kw}"
        suggestions = _fetch_raw_autocomplete(query_pattern, geo=geo, lang="id")
        for s in suggestions[:2]:
            clean_s = s.strip()
            if clean_s and clean_s not in results:
                results.append(clean_s)
        if len(results) >= 6:
            break

    # Tambahkan variasi suffix jika masih kurang
    if len(results) < 4:
        alt_patterns = [f"{core_kw} adalah", f"{core_kw} terbaru"]
        for alt in alt_patterns:
            suggestions = _fetch_raw_autocomplete(alt, geo=geo, lang="id")
            for s in suggestions[:2]:
                if s and s not in results:
                    results.append(s)

    # Fallback template kurasi jurnalistik Indonesia jika kueri Google Suggest minim
    if len(results) < 4:
        display_kw = core_kw.title()
        fallback_templates = [
            f"Apa penyebab dan faktor pemicu {display_kw}?",
            f"Bagaimana aturan dan regulasi terkait {display_kw}?",
            f"Kapan kebijakan {display_kw} mulai diberlakukan?",
            f"Apa dampak {display_kw} terhadap masyarakat?",
            f"Bagaimana langkah pencegahan dan solusi untuk {display_kw}?"
        ]
        for t in fallback_templates:
            if t not in results:
                results.append(t)
            if len(results) >= 6:
                break

    return results[:8]


def compare_keyword_trends(keywords: List[str], geo: str = "ID") -> Dict[str, Any]:
    """Membandingkan indikator pencarian beberapa kata kunci alternatif di Google Suggest & Trends."""
    comparison = {}

    for kw in keywords:
        kw_clean = kw.strip()
        if not kw_clean:
            continue
        suggestions = fetch_google_autocomplete(kw_clean, geo=geo)
        questions = fetch_people_also_ask(kw_clean, geo=geo)

        # Semakin banyak variasi autocomplete yang muncul, semakin tinggi search demand di Google
        demand_score = min(100, len(suggestions) * 10 + len(questions) * 5)
        status_label = "Sangat Tinggi" if demand_score >= 80 else "Tinggi" if demand_score >= 50 else "Cukup" if demand_score >= 20 else "Rendah"

        comparison[kw_clean] = {
            "search_demand_score": demand_score,
            "demand_level": status_label,
            "autocomplete_count": len(suggestions),
            "top_suggestions": suggestions[:5],
            "popular_questions": questions[:3]
        }

    # Tentukan pemenang rekomendasi kata kunci terbaik
    winner_kw = max(comparison.keys(), key=lambda k: comparison[k]["search_demand_score"]) if comparison else ""

    return {
        "status": "success",
        "recommended_keyword": winner_kw,
        "keywords_data": comparison
    }
