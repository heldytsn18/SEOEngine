import pytest
from app.services.html_service import analyze_html_structure
from app.services.scraper_service import generate_competitor_opportunities


def test_analyze_html_structure_scoped():
    # Simulasi halaman berita dengan widget sidebar dan template komentar
    html = """
    <html>
      <head><title>Test Berita</title></head>
      <body>
        <div class="sidebar">
          <h3>Berita Populer</h3>
          <img src="https://example.com/banner-sidebar.jpg" />
        </div>
        <article class="article-detail">
          <header class="article-header">
            <h1 class="article-title">Judul Berita Utama</h1>
          </header>
          <div class="article-content">
            <p>Paragraf pembuka berita yang memuat informasi awal peristiwa secara jelas dan padat.</p>
            <h2>Latar Belakang Acara</h2>
            <p>Penjelasan detail mengenai latar belakang acara yang berlangsung di Balikpapan.</p>
            <figure>
              <img src="https://example.com/foto-utama.jpg" alt="Foto kegiatan di Balikpapan" />
            </figure>
            <p>Penutupan artikel berita.</p>
            <div class="pagination-wrap">
              <a href="?view=all">Lihat semua</a>
            </div>
          </div>
          <div class="comments">
            <h3>Komentar (0)</h3>
            <h3>Kirim Komentar</h3>
          </div>
        </article>
      </body>
    </html>
    """

    res = analyze_html_structure(html, "Latar Belakang", base_url="https://example.com/berita", is_own_site=True)

    # Verifikasi headings: H2 terdeteksi, H3 komentar & sidebar terfilter
    assert res["headings"]["h2_count"] == 1
    assert "Latar Belakang Acara" in res["headings"]["h2_texts"]
    assert res["headings"]["h3_count"] == 0
    assert res["headings"]["keyword_in_subheading"] is True

    # Verifikasi images: Gambar banner sidebar tanpa alt diabaikan, hanya gambar artikel yang dihitung
    assert res["images"]["total"] == 1
    assert res["images"]["with_alt"] == 1
    assert res["images"]["without_alt"] == 0


def test_generate_competitor_opportunities_own_site():
    meta = {"word_count": 550, "meta_description": "Deskripsi meta valid"}
    tech = {"seo_score": 85}
    html_res = {
        "headings": {"h2_count": 0, "h3_count": 0, "keyword_in_subheading": False},
        "images": {"without_alt": 0},
        "links": {"external_count": 1}
    }
    kw_analysis = {
        "detected_competitor_keyword": "PEDA KTNA 2028",
        "recommended_focus_keyword": "PEDA KTNA Paser 2028",
        "keyword_variations": ["persiapan KTNA"]
    }

    # Uji mode web sendiri
    opps_own = generate_competitor_opportunities(
        meta, tech, html_res, "PEDA KTNA Paser 2028", kw_analysis, is_own_site=True
    )
    # Pastikan tidak ada kata 'kompetitor' di saran
    assert any("artikel Anda" in o for o in opps_own)
    assert not any("kompetitor" in o.lower() for o in opps_own)

    # Uji mode kompetitor
    opps_comp = generate_competitor_opportunities(
        meta, tech, html_res, "PEDA KTNA Paser 2028", kw_analysis, is_own_site=False
    )
    assert any("kompetitor" in o.lower() for o in opps_comp)
