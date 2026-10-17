import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.rewrite_service import calculate_text_similarity, rewrite_article_from_url

client = TestClient(app)


def test_calculate_text_similarity():
    text1 = "Pemerintah Kabupaten Paser menyatakan siap menjadi tuan rumah Pekan Daerah Kontak Tani Nelayan Andalan 2028."
    text2 = "Pemerintah Kabupaten Paser menyatakan siap menjadi tuan rumah Pekan Daerah Kontak Tani Nelayan Andalan 2028."
    # Teks identik harus memiliki kemiripan tinggi
    assert calculate_text_similarity(text1, text2) == 100.0

    text3 = "Polresta Balikpapan membongkar sindikat pencurian kendaraan bermotor di kawasan pasar tradisional kemarin sore."
    # Teks berbeda total harus mendekati 0%
    assert calculate_text_similarity(text1, text3) == 0.0

    # Teks sebagian
    text4 = "Wakil Bupati Paser menyambut hangat kedatangan pengurus tani nelayan di ruang rapat pemkab."
    sim = calculate_text_similarity(text1, text4)
    assert 0.0 <= sim <= 50.0


@patch("app.services.rewrite_service.extract_article_content")
@patch("app.services.rewrite_service.requests.post")
def test_rewrite_url_endpoint(mock_post, mock_extract):
    # Mock ekstraksi URL
    mock_extract.return_value = {
        "url": "https://kaltim.tribunnews.com/berita-unmul",
        "domain": "kaltim.tribunnews.com",
        "title": "Rudianto Terpilih Rektor Unmul Putaran Akhir",
        "text": "Samarinda - Pemilihan rektor Universitas Mulawarman selesai digelar di gedung rektorat lantai empat pada Selasa pagi. Proses pemilihan berlangsung khidmat dan tertib diikuti oleh seluruh anggota Senat Universitas Mulawarman serta perwakilan dari Kementerian Pendidikan Kebudayaan Riset dan Teknologi. Dalam pemungutan suara putaran akhir tersebut, Prof Rudianto Amirta berhasil meraih suara terbanyak mengungguli dua calon lainnya.",
        "meta_keywords": ["Rektor Unmul", "Rudianto Amirta"],
        "word_count": 300,
        "top_image": "https://kaltim.tribunnews.com/images/rektor-unmul.jpg"
    }

    # Mock response 9Router AI
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{
            "message": {
                "content": """{
                    "title": "Rudianto Amirta Terpilih Jadi Rektor Unmul 2026-2030",
                    "title_alternatives": ["Hasil Sidang Senat Unmul: Rudianto Unggul 74 Suara"],
                    "lede": "SAMARINDA - Guru Besar Fakultas Kehutanan, Prof Rudianto Amirta, terpilih memimpin Unmul.",
                    "content_html": "<p>SAMARINDA - Guru Besar Fakultas Kehutanan...</p><h2>Hasil Sidang Senat</h2><p>Pelaksanaan pemilihan berlangsung demokratis...</p>",
                    "content_plain": "SAMARINDA - Guru Besar Fakultas Kehutanan...\\n\\nHasil Sidang Senat\\n\\nPelaksanaan pemilihan berlangsung demokratis...",
                    "focus_keyword": "Rektor Unmul 2026",
                    "keyword_variations": ["Pemilihan Rektor Unmul", "Rudianto Amirta"],
                    "meta_description": "Prof Rudianto Amirta terpilih sebagai Rektor Unmul 2026-2030 setelah unggul dalam pemungutan suara Senat.",
                    "suggested_category": "Pendidikan",
                    "suggested_tags": ["Unmul", "Rektor Unmul", "Samarinda"]
                }"""
            }
        }]
    }

    res = client.post("/api/v1/seo/rewrite-url", json={
        "url": "https://kaltim.tribunnews.com/berita-unmul",
        "focus_keyword": "Rektor Unmul 2026"
    })

    assert res.status_code == 200
    data = res.json()["data"]
    assert "article" in data
    assert "seo_metadata" in data
    assert "quality_metrics" in data
    assert "source_metadata" in data
    assert data["article"]["title"] == "Rudianto Amirta Terpilih Jadi Rektor Unmul 2026-2030"
    assert "content" in data["article"]
    assert data["article"]["featured_image_url"] == "https://kaltim.tribunnews.com/images/rektor-unmul.jpg"
    assert data["seo_metadata"]["focus_keyword"] == "Rektor Unmul 2026"
    assert data["source_metadata"]["source_domain"] == "kaltim.tribunnews.com"
    assert data["source_metadata"]["source_image"] == "https://kaltim.tribunnews.com/images/rektor-unmul.jpg"
    assert "attribution_quote" in data["source_metadata"]


def test_rewrite_url_ssrf_protection():
    # URL lokal/private harus ditolak dengan status 400
    res = client.post("/api/v1/seo/rewrite-url", json={"url": "http://127.0.0.1:8000/secret"})
    assert res.status_code == 400
    assert "tidak diizinkan" in res.json()["detail"].lower()


@patch("app.services.rewrite_service.extract_article_content")
def test_rewrite_url_short_text_rejected(mock_extract):
    mock_extract.return_value = {
        "url": "https://example.com/blocked",
        "domain": "example.com",
        "title": "Blocked",
        "text": "Please enable JavaScript to view this website.",
        "meta_keywords": [],
        "word_count": 7
    }

    res = client.post("/api/v1/seo/rewrite-url", json={"url": "https://example.com/blocked"})
    assert res.status_code == 400
    assert "terlalu pendek" in res.json()["detail"].lower()
