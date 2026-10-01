import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["components"]["fastapi"] == "ready"


def test_analyze_article_local_heuristics():
    payload = {
        "title": "Kemnaker Dorong Generasi Muda Balikpapan Kuasai AI untuk Tingkatkan Produktivitas Kerja",
        "content": (
            "<p>BALIKPAPAN - Kementerian Ketenagakerjaan mendorong generasi muda di Balikpapan untuk "
            "menguasai teknologi kecerdasan buatan (AI) guna meningkatkan produktivitas kerja di era digital, Rabu (1/10/2026).</p>"
            "<p>Pelatihan ini diharapkan memperkuat daya saing tenaga kerja lokal di pasar global.</p>"
            "<p>Kepala Dinas Ketenagakerjaan Balikpapan menegaskan komitmen pemerintah dalam mendampingi para pencari kerja muda.</p>"
        ),
        "focus_keyword": "AI generasi muda produktivitas",
        "category": "Teknologi",
        "use_ai_analysis": False
    }

    response = client.post("/api/v1/seo/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert "data" in res

    data = res["data"]
    assert "news_analysis" in data
    assert "seo_suggestions" in data
    assert "combined_suggestions" in data

    na = data["news_analysis"]
    assert na["keyword_coverage"] == 100.0
    assert na["lede_has_5w1h"] is True
    assert na["lede_quality"] == "Good"
    assert 0 <= na["readability_score"] <= 100
    assert 0 <= data["overall_score"] <= 100


def test_schema_jsonld():
    payload = {
        "title": "Polri Tindak Lanjut Judi Online di Kaltim",
        "description": "Kepolisian Daerah Kaltim melakukan tindakan tegas terhadap pelaku judi online.",
        "author_name": "Redaksi BorneoFlash",
        "publisher_name": "BorneoFlash Media",
        "publisher_logo_url": "https://borneoflash.com/logo.png",
        "date_published": "2026-10-01T10:00:00+08:00",
        "article_url": "https://borneoflash.com/polri-judi-online-kaltim"
    }

    response = client.post("/api/v1/seo/schema-jsonld", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["data"]["jsonld"]["@type"] == "NewsArticle"
    assert '<script type="application/ld+json">' in res["data"]["html_snippet"]


def test_analyze_url_tribunnews():
    payload = {
        "url": "https://kaltim.tribunnews.com/tribun-etam/1168317/rudianto-salip-abdunnur-di-putaran-akhir-74-suara-antarkan-guru-besar-kehutanan-jadi-rektor-unmul",
        "focus_keyword": "",  # Kosong sesuai skenario pengguna
        "use_ai_analysis": False
    }

    response = client.post("/api/v1/seo/analyze-url", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    data = res["data"]
    assert "url_metadata" in data
    assert "Rudianto" in data["url_metadata"]["title"]
    assert data["url_metadata"]["domain"] == "kaltim.tribunnews.com"
    assert data["url_metadata"]["word_count"] > 100

    # Verifikasi keyword_analysis
    assert "keyword_analysis" in data
    ka = data["keyword_analysis"]
    assert ka["detected_competitor_keyword"] != ""
    assert "Pemilihan Rektor" in ka["detected_competitor_keyword"] or "Rudianto" in ka["detected_competitor_keyword"]
    assert ka["recommended_focus_keyword"] != ""
    assert data["seo_suggestions"]["focus_keyword"] == ka["recommended_focus_keyword"]

    # Verifikasi competitor_opportunities memuat saran kata kunci
    assert "competitor_opportunities" in data
    assert len(data["competitor_opportunities"]) > 0
    assert any("kata kunci" in opp.lower() for opp in data["competitor_opportunities"])
