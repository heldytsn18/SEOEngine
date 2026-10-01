import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.improvement_service import improve_article_content

client = TestClient(app)


@patch("app.services.improvement_service.requests.post")
def test_improve_content_with_ai(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{
            "message": {
                "content": """{
                    "title": "Paser Siap Tuan Rumah PEDA KTNA 2028, Dorong Pertanian",
                    "title_alternatives": ["Wabup Paser Kebut Persiapan PEDA KTNA 2028"],
                    "lede": "TANA PASER - Pemerintah Kabupaten Paser menyatakan kesiapan menyambut PEDA KTNA 2028 dalam pertemuan bersama pengurus provinsi.",
                    "content_html": "<p>TANA PASER - Pemerintah Kabupaten Paser menyatakan kesiapan...</p><h2>Fokus Persiapan PEDA KTNA 2028</h2><p>Pemerintah daerah mulai memetakan zonasi acara...</p>",
                    "content_plain": "TANA PASER - Pemerintah Kabupaten Paser menyatakan kesiapan...\\n\\nFokus Persiapan PEDA KTNA 2028\\n\\nPemerintah daerah mulai memetakan zonasi acara...",
                    "meta_description": "Pemkab Paser siap helat PEDA KTNA 2028. Wabup Ikhwan Antasari targetkan dampak ekonomi bagi petani dan nelayan lokal.",
                    "improvements_applied": [
                        "Memecah kalimat panjang menjadi kalimat efektif.",
                        "Menyisipkan kata kunci fokus di pembuka dan subjudul H2."
                    ]
                }"""
            }
        }]
    }

    res = client.post("/api/v1/seo/improve-content", json={
        "title": "Tatap PEDA KTNA 2028, Wabup Paser Terima Audiensi Pengurus Provinsi dan Kabupaten",
        "content": "Pemerintah Kabupaten Paser secara resmi menyatakan kesiapannya untuk melakoni peran sebagai tuan rumah helatan akbar Pekan Daerah Kontak Tani Nelayan Andalan XII Kalimantan Timur yang dijadwalkan bergulir pada tahun 2028 mendatang demi kemajuan bersama.",
        "focus_keyword": "PEDA KTNA 2028",
        "mode": "all"
    })

    assert res.status_code == 200
    data = res.json()["data"]
    assert "improved_article" in data
    assert "improvements_applied" in data
    assert "score_comparison" in data
    assert data["improved_article"]["title"] == "Paser Siap Tuan Rumah PEDA KTNA 2028, Dorong Pertanian"
    assert "before" in data["score_comparison"]
    assert "after" in data["score_comparison"]
    assert "score_gain" in data["score_comparison"]


def test_improve_content_empty_validation():
    res = client.post("/api/v1/seo/improve-content", json={
        "title": "Judul Kosong",
        "content": "   "
    })
    assert res.status_code == 400


@patch("app.services.improvement_service.requests.post")
def test_improve_content_fallback_heuristic(mock_post):
    # Simulasikan kegagalan jaringan ke AI
    mock_post.side_effect = Exception("Connection timeout")

    res = client.post("/api/v1/seo/improve-content", json={
        "title": "Judul Uji Coba Berita",
        "content": "Paragraf pertama berita uji coba yang cukup panjang untuk diuji dengan sistem evaluasi SEO lokal.",
        "focus_keyword": "Berita Uji Coba"
    })

    assert res.status_code == 200
    data = res.json()["data"]
    assert "improved_article" in data
    assert len(data["improvements_applied"]) > 0
