from typing import Optional, Dict, Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.services.technical_service import clean_text, STOPWORDS_ID


def analyze_html_structure(html_content: str, keyword: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Analisis struktur HTML: heading tags, image alt text, dan link audit."""
    soup = BeautifulSoup(html_content, "html.parser")
    cleaned_keyword = clean_text(keyword)
    keyword_words = [w for w in cleaned_keyword.split() if w not in STOPWORDS_ID]

    # --- Heading Tag Inspection ---
    headings = {"h2": [], "h3": []}
    keyword_in_subheading = False

    for tag in ("h2", "h3"):
        for el in soup.find_all(tag):
            text = el.get_text(strip=True)
            headings[tag].append(text)
            cleaned_heading = clean_text(text)
            heading_words = set(cleaned_heading.split())
            if keyword_words and all(w in heading_words for w in keyword_words):
                keyword_in_subheading = True

    total_subheadings = len(headings["h2"]) + len(headings["h3"])

    # --- Image Alt Text Audit ---
    images = soup.find_all("img")
    total_images = len(images)
    images_without_alt = []
    images_with_alt = []

    for img in images:
        src = img.get("src") or img.get("data-src") or "[Gambar tanpa URL]"
        alt = img.get("alt", "").strip()
        if not alt:
            images_without_alt.append(src)
        else:
            images_with_alt.append({"src": src, "alt": alt})

    # --- Link Audit ---
    links = soup.find_all("a", href=True)
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
        href = link["href"]
        link_text = link.get_text(strip=True)

        if href.startswith("#") or href.startswith("javascript:"):
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

    # --- Skor & Saran ---
    suggestions = []
    kw_display = keyword.strip() if keyword else "Topik Berita"

    if total_subheadings == 0:
        suggestions.append(f"Tidak ditemukan tag <h2> atau <h3>. Tambahkan subheading untuk memecah struktur artikel, contoh: <h2>Latar Belakang dan Dampak {kw_display}</h2>.")
    elif not keyword_in_subheading:
        suggestions.append(f"Kata kunci fokus belum ada di subheading. Sisipkan kata kunci di minimal satu subheading (<h2>/<h3>), contoh: <h2>Perkembangan {kw_display} Terkini</h2>.")

    if total_images == 0:
        suggestions.append(f"Tidak ada gambar ditemukan. Tambahkan gambar pendukung dengan alt text relevan, contoh alt: 'Dokumentasi terkait {kw_display}'.")
    elif images_without_alt:
        suggestions.append(f"{len(images_without_alt)} dari {total_images} gambar tidak memiliki atribut alt text. Tambahkan deskripsi gambar yang relevan dengan isi berita.")

    if len(external_links) == 0:
        suggestions.append("Tidak ada external link ke sumber rujukan. Tambahkan tautan ke sumber resmi (misal situs kementerian, BPS, atau instansi terkait) untuk memperkuat E-E-A-T.")

    return {
        "headings": {
            "h2_count": len(headings["h2"]),
            "h3_count": len(headings["h3"]),
            "h2_texts": headings["h2"],
            "h3_texts": headings["h3"],
            "keyword_in_subheading": keyword_in_subheading
        },
        "images": {
            "total": total_images,
            "with_alt": len(images_with_alt),
            "without_alt": len(images_without_alt),
            "missing_alt_sources": images_without_alt[:10]  # Batasi 10 untuk response
        },
        "links": {
            "internal_count": len(internal_links),
            "external_count": len(external_links),
            "external_domains": sorted(external_domains),
        },
        "html_suggestions": suggestions
    }
