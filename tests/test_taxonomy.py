import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_analyze_taxonomy_category_local():
    payload = {
        "name": "Balikpapan Pos",
        "description": "Kumpulan berita seputar Kota Balikpapan dan Kalimantan Timur.",
        "taxonomy_type": "category",
        "use_ai_analysis": False
    }

    response = client.post("/api/v1/seo/analyze-taxonomy", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["provider"] == "local"

    data = res["data"]
    assert "seo_title" in data
    assert "meta_description" in data
    assert "focus_keyword" in data
    assert "improved_description" in data
    assert "suggestions" in data
    assert 0 <= data["seo_score"] <= 100
    assert 0 <= data["readability_score"] <= 100
    assert "Balikpapan Pos" in data["seo_title"]


def test_analyze_taxonomy_tag_local():
    payload = {
        "name": "Judi Online",
        "description": "Berita penindakan kasus judi online oleh Polda Kaltim.",
        "taxonomy_type": "post_tag",
        "use_ai_analysis": False
    }

    response = client.post("/api/v1/seo/analyze-taxonomy", json=payload)
    assert response.status_code == 200
    res = response.json()
    data = res["data"]
    assert "Kumpulan Berita" in data["seo_title"]
    assert data["focus_keyword"] == "berita judi online"


def test_analyze_taxonomy_empty_name():
    payload = {
        "name": "   ",
        "description": "Deskripsi tanpa nama",
        "taxonomy_type": "category",
        "use_ai_analysis": False
    }

    response = client.post("/api/v1/seo/analyze-taxonomy", json=payload)
    assert response.status_code == 400
    assert "tidak boleh kosong" in response.json()["detail"].lower()


def test_analyze_taxonomy_missing_desc_suggestion():
    payload = {
        "name": "Kaltim Berdaulat",
        "description": "",
        "taxonomy_type": "newstopic",
        "use_ai_analysis": False
    }

    response = client.post("/api/v1/seo/analyze-taxonomy", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    # Deskripsi kosong harus memicu penalti dan saran pembuatan deskripsi
    assert data["seo_score"] < 80
    assert any("deskripsi" in s.lower() and "kosong" in s.lower() for s in data["suggestions"])
    assert len(data["improved_description"]) > 50
