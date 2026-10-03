import re
import copy
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import logging

from bs4 import BeautifulSoup

from app.services.technical_service import clean_text, STOPWORDS_ID

logger = logging.getLogger(__name__)

TEMPLATE_HEADING_PATTERN = re.compile(
    r'^(komentar(\s*\(\d+\))?|kirim\s*komentar|tulis\s*komentar|baca\s*juga|'
    r'berita\s*(terkini|populer|terkait|terbaru|lainnya)|'
    r'(artikel|posting|topik|tag)\s*terkait|'
    r'video\s*(populer|terkini|terbaru)|'
    r'tetap\s*(terhubung|update)|'
    r'(baca|lihat)\s*(juga|lainnya)|'
    r'trending|populer|terkini|ikuti\s*kami|iklan|advertisement|disclaimer|share|rekomendasi)',
    re.I
)


def analyze_html_structure(
    html_content: str,
    keyword: str,
    base_url: Optional[str] = None,
    is_own_site: bool = False
) -> Dict[str, Any]:
    """Analisis struktur HTML: heading tags, image alt text, dan link audit ter-scope pada artikel."""
    soup = BeautifulSoup(html_content, "html.parser")
    cleaned_keyword = clean_text(keyword)
    keyword_words = [w for w in cleaned_keyword.split() if w not in STOPWORDS_ID]

    # --- 1. Scoping Kontainer Artikel & Pembersihan Noise ---
    # Buang elemen global non-konten dari halaman
    for unwanted in soup.select(
        "header.site-header, footer, nav, aside, .sidebar, .widget-area, .content-ad-sticky, .comments, #comments"
    ):
        unwanted.decompose()

    article_container = (
        soup.select_one("article.article-detail") or
        soup.select_one("article") or
        soup.select_one("[itemprop='articleBody']") or
        soup.select_one(".article-content") or
        soup.select_one(".read__content") or
        soup.select_one(".side-article.txt-article") or
        soup.select_one(".detail__body-text") or
        soup.select_one(".entry-content") or
        soup.select_one(".post-content")
    )

    target_dom = copy.copy(article_container) if article_container else soup

    # Buang noise di dalam kontainer artikel (widget iklan, share buttons, tags, navigasi pos)
    for unwanted in target_dom.select(
        "script, style, noscript, .ads, .adsbygoogle, .gmr-ad-in-article, "
        ".baca-juga, .related, .related-list-section, .article-tags, .tags, "
        ".share, .article-share-sidebar, .share-buttons-meta, .post-navigation, "
        ".pagination-wrap, header.article-header"
    ):
        unwanted.decompose()

    # --- 2. Heading Tag Inspection (Filter out Template UI Headings) ---
    headings = {"h2": [], "h3": []}
    keyword_in_subheading = False

    for tag in ("h2", "h3"):
        for el in target_dom.find_all(tag):
            text = el.get_text(strip=True)
            if not text or TEMPLATE_HEADING_PATTERN.search(text.lower()):
                continue
            headings[tag].append(text)
            cleaned_heading = clean_text(text)
            heading_words = set(cleaned_heading.split())
            if keyword_words and all(w in heading_words for w in keyword_words):
                keyword_in_subheading = True

    total_subheadings = len(headings["h2"]) + len(headings["h3"])

    # --- 3. Image Alt Text Audit (Khusus Gambar Artikel) ---
    images = target_dom.find_all("img")
    valid_images = []
    images_without_alt = []
    images_with_alt = []

    for img in images:
        src = img.get("src") or img.get("data-src") or ""
        # Abaikan tracker, icon, avatar, logo, atau banner tombol iklan non-konten
        if any(ign in src.lower() for ign in ["avatar", "icon", "logo", "button", "badge", "tracker", "data:image", "click-here", "arsip"]):
            continue
        w = img.get("width")
        h = img.get("height")
        if w and str(w).isdigit() and int(w) <= 5:
            continue
        if h and str(h).isdigit() and int(h) <= 5:
            continue

        alt = img.get("alt", "").strip()
        img_info = {"src": src or "[Gambar tanpa URL]", "alt": alt}
        valid_images.append(img_info)

        if not alt:
            images_without_alt.append(img_info["src"])
        else:
            images_with_alt.append(img_info)

    total_valid_images = len(valid_images)

    # --- 4. Link Audit (Fokus Pada Tautan Konten Artikel) ---
    links = target_dom.find_all("a", href=True)
    internal_links = []
    external_links = []
    external_domains = set()

    base_domain = ""
    if base_url:
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc.lower()
        if base_domain.startswith("www."):
            base_domain = base_domain[4:]

    for link in links:
        href = link["href"].strip()
        link_text = link.get_text(strip=True)

        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue

        parsed = urlparse(href)
        link_domain = parsed.netloc.lower()
        if link_domain.startswith("www."):
            link_domain = link_domain[4:]

        if not link_domain or link_domain == base_domain:
            internal_links.append({"href": href, "text": link_text})
        else:
            external_links.append({"href": href, "text": link_text, "domain": link_domain})
            external_domains.add(link_domain)

    # --- 5. Skor & Saran ---
    suggestions = []
    kw_display = keyword.strip() if keyword else "Topik Berita"
    subject = "naskah artikel Anda" if is_own_site else "badan artikel"

    if total_subheadings == 0:
        suggestions.append(
            f"Tidak ditemukan tag H2 atau H3 di {subject}. Tambahkan subheading untuk memecah struktur naskah, contoh: 'Latar Belakang dan Dampak {kw_display}'."
        )
    elif not keyword_in_subheading:
        suggestions.append(
            f"Kata kunci fokus belum ada di subheading. Sisipkan kata kunci di minimal satu subheading (H2/H3), contoh: 'Perkembangan {kw_display} Terkini'."
        )

    if total_valid_images == 0:
        suggestions.append(
            f"Tidak ada gambar artikel ditemukan. Tambahkan gambar pendukung dengan alt text relevan, contoh alt: 'Dokumentasi terkait {kw_display}'."
        )
    elif images_without_alt:
        suggestions.append(
            f"{len(images_without_alt)} dari {total_valid_images} gambar artikel tidak memiliki atribut alt text. Tambahkan deskripsi gambar yang relevan dengan isi berita."
        )

    if len(external_links) == 0:
        suggestions.append(
            "Tidak ada external link rujukan di dalam artikel. Tambahkan tautan ke sumber resmi (misal situs kementerian, BPS, atau instansi terkait) untuk memperkuat E-E-A-T."
        )

    return {
        "headings": {
            "h2_count": len(headings["h2"]),
            "h3_count": len(headings["h3"]),
            "h2_texts": headings["h2"],
            "h3_texts": headings["h3"],
            "keyword_in_subheading": keyword_in_subheading
        },
        "images": {
            "total": total_valid_images,
            "with_alt": len(images_with_alt),
            "without_alt": len(images_without_alt),
            "missing_alt_sources": images_without_alt[:10]
        },
        "links": {
            "internal_count": len(internal_links),
            "external_count": len(external_links),
            "external_domains": sorted(external_domains),
        },
        "html_suggestions": suggestions
    }
