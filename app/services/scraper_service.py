import re
import copy
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from newspaper import Article

# Daftar User-Agent browser modern untuk melewati blokir WAF / anti-bot
BROWSER_USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
    ),
    (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Mobile Safari/537.36"
    ),
]


def fetch_html_with_browser_headers(url: str, timeout: int = 20) -> str:
    """Mengambil HTML halaman artikel dengan browser headers realistis untuk mencegah blokir 403 Forbidden."""
    last_error = None

    for ua in BROWSER_USER_AGENTS:
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "Sec-Ch-Ua-Mobile": "?0" if "Mobile" not in ua else "?1",
            "Sec-Ch-Ua-Platform": '"Windows"' if "Windows" in ua else ('"macOS"' if "Macintosh" in ua else '"Android"'),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

        try:
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200:
                # Pastikan encoding teks terdeteksi dengan tepat
                if resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
                    resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            elif resp.status_code in (403, 401, 429):
                last_error = f"HTTP {resp.status_code} (Akses dibatasi WAF/Cloudflare portal)"
                continue
            else:
                last_error = f"HTTP {resp.status_code}: {resp.reason}"
        except Exception as e:
            last_error = str(e)

    raise Exception(f"Gagal mengambil halaman dari URL: {last_error}")


def extract_article_content(url: str, html: Optional[str] = None) -> Dict[str, Any]:
    """Ekstraksi teks berita, metadata, dan struktur konten dari URL kompetitor atau web sendiri."""
    if not html:
        html = fetch_html_with_browser_headers(url)

    # 1. Deteksi Paginasi (Lihat semua / Semua Halaman / view=all / page=all / single=1)
    soup_initial = BeautifulSoup(html, "html.parser")
    view_all_url = None
    for a in soup_initial.find_all("a", href=True):
        href = a["href"].strip()
        link_text = a.get_text(strip=True).lower()
        if (
            "view=all" in href.lower()
            or "page=all" in href.lower()
            or "single=1" in href.lower()
            or link_text in ["lihat semua", "semua halaman", "all pages", "view all", "baca semua", "tampilkan semua", "full page"]
        ):
            candidate = urljoin(url, href)
            if candidate != url and candidate != url + "/" and candidate != url.rstrip("/"):
                view_all_url = candidate
                break

    if view_all_url:
        try:
            full_html = fetch_html_with_browser_headers(view_all_url)
            if full_html and len(full_html) > len(html) * 0.8:
                html = full_html
        except Exception:
            pass

    # 2. Parsing menggunakan newspaper4k dengan custom input_html
    article = Article(url)
    try:
        article.download(input_html=html)
        article.parse()
    except Exception:
        pass

    title = (article.title or "").strip()
    text = (article.text or "").strip()
    authors = article.authors or []
    publish_date = str(article.publish_date) if article.publish_date else None
    top_image = article.top_image or ""

    # 3. Ekstraksi Metadata Lanjutan & Fallback Scoped via BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Fallback Judul jika newspaper gagal
    if not title:
        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        elif soup.title:
            title = soup.title.get_text(strip=True)

    # Bersihkan akhiran judul brand media (contoh: "... - Tribun Kaltim", "... | Kompas.com")
    title_clean = re.sub(
        r'\s*[-|–—]\s*(Tribun\s*Kaltim|Kompas\.com|Detikcom|Kaltim\s*Post|Kaltimtoday|BorneoFlash\.com|BorneoFlash).*$',
        '',
        title,
        flags=re.IGNORECASE
    ).strip()
    if title_clean:
        title = title_clean

    # Ekstraksi Paragraf Bersih Ter-scope dari Kontainer Artikel
    content_selectors = [
        "article.article-detail .article-content",
        "article .article-content",
        "article.article-detail",
        "article",
        "[itemprop='articleBody']",
        ".side-article.txt-article",
        ".read__content",
        ".detail__body-text",
        ".post-content",
        ".entry-content",
        ".content",
        ".article-content"
    ]
    extracted_paras = []
    for selector in content_selectors:
        container = soup.select_one(selector)
        if container:
            c = copy.copy(container)
            # Buang elemen iklan, skrip, dan navigasi di dalam kontainer
            for unwanted in c.select(
                "script, style, noscript, .ads, .adsbygoogle, .gmr-ad-in-article, "
                ".baca-juga, .related, .related-list-section, .tags, .article-tags, "
                ".share, .article-share-sidebar, .share-buttons-meta, .post-navigation, "
                ".pagination-wrap, .widget-area, .content-ad-sticky"
            ):
                unwanted.decompose()
            paras = []
            for p in c.find_all("p"):
                raw_p = p.get_text(separator=" ", strip=True)
                clean_p = re.sub(r'\s+', ' ', raw_p).strip()
                clean_p = re.sub(r'\s+([,.:;!?)])', r'\1', clean_p)
                clean_p = re.sub(r'([(])\s+', r'\1', clean_p)
                if len(clean_p.split()) >= 4:
                    paras.append(clean_p)
            if paras:
                extracted_paras = paras
                break

    if not extracted_paras:
        # Fallback: kumpulkan semua paragraf valid di dokumen luar
        paras = []
        for p in soup.find_all("p"):
            raw_p = p.get_text(separator=" ", strip=True)
            clean_p = re.sub(r'\s+', ' ', raw_p).strip()
            clean_p = re.sub(r'\s+([,.:;!?)])', r'\1', clean_p)
            clean_p = re.sub(r'([(])\s+', r'\1', clean_p)
            if len(clean_p.split()) >= 5:
                paras.append(clean_p)
        extracted_paras = paras

    if extracted_paras:
        bs4_text = "\n\n".join(extracted_paras)
        # Jika BS4 mengekstrak lebih banyak kata atau newspaper kosong, utamakan BS4
        if not text or len(bs4_text.split()) > len(text.split()):
            text = bs4_text

    # Ekstraksi Meta Description
    meta_desc = ""
    desc_tag = (
        soup.find("meta", attrs={"name": "description"}) or
        soup.find("meta", property="og:description") or
        soup.find("meta", attrs={"name": "twitter:description"})
    )
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    # Ekstraksi Canonical URL
    canonical_url = url
    canon_tag = soup.find("link", attrs={"rel": "canonical"})
    if canon_tag and canon_tag.get("href"):
        canonical_url = canon_tag["href"].strip()

    # Ekstraksi Penulis jika kosong
    if not authors:
        author_tag = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if author_tag and author_tag.get("content"):
            authors = [author_tag["content"].strip()]

    # Ekstraksi Gambar jika kosong
    if not top_image:
        img_tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if img_tag and img_tag.get("content"):
            top_image = img_tag["content"].strip()

    # Ekstraksi Tanggal Terbit jika kosong
    if not publish_date:
        date_tag = (
            soup.find("meta", property="article:published_time") or
            soup.find("meta", attrs={"name": "pubdate"}) or
            soup.find("time")
        )
        if date_tag:
            publish_date = date_tag.get("datetime") or date_tag.get("content") or date_tag.get_text(strip=True)

    # Ekstraksi Meta Keywords (Kata kunci yang ditargetkan kompetitor)
    meta_keywords = []
    kw_tags = soup.find_all("meta", attrs={"name": re.compile(r'^(keywords|news_keywords)$', re.I)})
    for tag in kw_tags:
        content_val = tag.get("content", "")
        if content_val:
            for item in content_val.split(","):
                clean_item = item.strip()
                if clean_item and clean_item.lower() not in [k.lower() for k in meta_keywords]:
                    meta_keywords.append(clean_item)

    for tag in soup.find_all("meta", property="article:tag"):
        content_val = tag.get("content", "")
        if content_val and content_val.strip().lower() not in [k.lower() for k in meta_keywords]:
            meta_keywords.append(content_val.strip())

    words = text.split()
    word_count = len(words)
    reading_time = max(1, round(word_count / 180))

    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    detected_keyword_heuristic = meta_keywords[0] if meta_keywords else ""

    return {
        "url": url,
        "domain": domain,
        "title": title,
        "text": text,
        "html": html,
        "authors": authors,
        "publish_date": publish_date,
        "top_image": top_image,
        "meta_description": meta_desc,
        "meta_keywords": meta_keywords,
        "detected_keyword_heuristic": detected_keyword_heuristic,
        "canonical_url": canonical_url,
        "word_count": word_count,
        "reading_time_minutes": reading_time
    }


def generate_competitor_opportunities(
    competitor_meta: Dict[str, Any],
    technical_res: Dict[str, Any],
    html_res: Dict[str, Any],
    keyword: str,
    keyword_analysis: Optional[Dict[str, Any]] = None,
    is_own_site: bool = False
) -> List[str]:
    """Menghasilkan catatan intelijen redaksi (Peluang Menyalip Kompetitor atau Rekomendasi Audit Internal)."""
    opportunities: List[str] = []
    word_count = competitor_meta.get("word_count", 0)
    kw_display = keyword.strip() if keyword else "topik ini"

    # 1. Celah & Rekomendasi Kata Kunci Target (Keyword Gap)
    if keyword_analysis:
        det_kw = keyword_analysis.get("detected_competitor_keyword")
        rec_kw = keyword_analysis.get("recommended_focus_keyword")
        variations = keyword_analysis.get("keyword_variations", [])
        var_str = f" (variasi: {', '.join(variations[:3])})" if variations else ""

        if is_own_site:
            if det_kw and rec_kw and det_kw.lower() != rec_kw.lower():
                opportunities.append(
                    f"Kata kunci terdeteksi pada naskah artikel Anda: '{det_kw}'. Untuk mendongkrak peringkat artikel ini di Google, optimasi menggunakan rekomendasi kata kunci fokus: '{rec_kw}'{var_str}."
                )
            elif rec_kw:
                opportunities.append(
                    f"Rekomendasi kata kunci fokus terbaik untuk memperkuat SEO artikel Anda: '{rec_kw}'{var_str}."
                )
        else:
            if det_kw and rec_kw and det_kw.lower() != rec_kw.lower():
                opportunities.append(
                    f"Kata kunci terdeteksi yang dibidik kompetitor: '{det_kw}'. Untuk menyalip di hasil pencarian atau mengoptimasi artikel sendiri, gunakan rekomendasi kata kunci fokus: '{rec_kw}'{var_str}."
                )
            elif rec_kw:
                opportunities.append(
                    f"Rekomendasi kata kunci fokus terbaik untuk SEO artikel ini: '{rec_kw}'{var_str}."
                )

    # 2. Celah Kedalaman Konten (Content Depth Gap)
    if is_own_site:
        if word_count < 300:
            opportunities.append(
                f"Naskah artikel Anda sangat singkat (hanya {word_count} kata). Kembangkan naskah minimal 400-500 kata agar berbobot dan diprioritaskan Google News."
            )
        elif word_count < 500:
            opportunities.append(
                f"Panjang naskah Anda saat ini {word_count} kata. Tambahkan sudut pandang eksklusif atau latar belakang peristiwa untuk memperkuat kedalaman liputan."
            )
    else:
        if word_count < 300:
            opportunities.append(
                f"Artikel kompetitor sangat singkat (hanya {word_count} kata). Tulis liputan mendalam minimal 400-500 kata untuk peluang besar mengungguli peringkatnya di Google."
            )
        elif word_count < 500:
            opportunities.append(
                f"Panjang artikel kompetitor standar ({word_count} kata). Tambahkan sudut pandang eksklusif atau latar belakang peristiwa untuk menyalipnya."
            )

    # 3. Celah Struktur Heading
    headings = html_res.get("headings", {})
    total_headings = headings.get("h2_count", 0) + headings.get("h3_count", 0)
    if is_own_site:
        if total_headings == 0:
            opportunities.append(
                f"Naskah artikel Anda belum dipecah dengan subheading H2/H3. Susun artikel Anda dengan minimal 1-2 subjudul H2 yang memuat '{kw_display}'."
            )
        elif not headings.get("keyword_in_subheading"):
            opportunities.append(
                f"Naskah Anda belum memasukkan kata kunci '{kw_display}' di subheading H2. Sisipkan kata kunci pada salah satu subjudul artikel."
            )
    else:
        if total_headings == 0:
            opportunities.append(
                f"Kompetitor tidak memecah artikel dengan subheading H2/H3. Susun artikel Anda dengan minimal 2 subjudul bernas yang memuat '{kw_display}'."
            )
        elif not headings.get("keyword_in_subheading"):
            opportunities.append(
                f"Kompetitor belum memasukkan kata kunci '{kw_display}' di subheading H2. Manfaatkan celah ini di struktur naskah Anda."
            )

    # 4. Celah Tautan Rujukan (E-E-A-T Link Gap)
    links = html_res.get("links", {})
    if links.get("external_count", 0) == 0:
        if is_own_site:
            opportunities.append(
                "Artikel Anda belum mencantumkan tautan ke sumber resmi/pemerintah. Cantumkan rujukan resmi untuk memperkuat skor E-E-A-T di Google News."
            )
        else:
            opportunities.append(
                "Kompetitor tidak mencantumkan tautan ke sumber resmi/pemerintah. Cantumkan rujukan resmi untuk skor E-E-A-T yang lebih kuat di Google News."
            )

    # 5. Celah Optimasi Gambar
    images = html_res.get("images", {})
    if images.get("without_alt", 0) > 0:
        if is_own_site:
            opportunities.append(
                f"Terdapat {images.get('without_alt')} gambar di artikel Anda tanpa alt text. Lengkapi seluruh foto dengan alt text yang memuat '{kw_display}'."
            )
        else:
            opportunities.append(
                f"Kompetitor memiliki {images.get('without_alt')} gambar tanpa alt text. Pastikan seluruh foto di artikel Anda dilengkapi deskripsi alt text yang memuat '{kw_display}'."
            )

    # 6. Celah Meta Description
    if not competitor_meta.get("meta_description"):
        if is_own_site:
            opportunities.append(
                "Artikel Anda belum memiliki meta description yang terkonfigurasi rapi. Buat ringkasan meta 130-150 karakter yang memancing klik di hasil pencarian."
            )
        else:
            opportunities.append(
                "Kompetitor tidak mengonfigurasi meta description dengan rapi. Buat ringkasan meta 130-150 karakter yang memancing klik di hasil pencarian."
            )

    if not opportunities:
        if is_own_site:
            opportunities.append(
                "Artikel Anda sudah teroptimasi dengan sangat baik. Pastikan penulisan judul menarik perhatian pembaca dan sebarkan segera."
            )
        else:
            opportunities.append(
                f"Artikel kompetitor sudah cukup teroptimasi. Prioritaskan judul yang lebih menarik klik dan kecepatan tayang untuk merebut perhatian pembaca."
            )

    return opportunities
