import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


def test_root_and_health_v3():
    """Memastikan metadata aplikasi telah di-upgrade ke v3.0.0"""
    res_root = client.get("/")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["version"] == "3.0.0"
    assert "Google Trends Realtime & Autocomplete" in data_root["modules"]

    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["version"] == "3.0.0"
    assert "components" in data_health
    assert data_health["components"]["google_trends"] == "ready"


def test_trends_daily():
    """Menguji endpoint Google Trends Daily"""
    with patch("app.routers.trends.fetch_daily_trends") as mock_fetch:
        mock_fetch.return_value = [
            {
                "title": "Insentif Guru PAUD Samarinda",
                "traffic": "50K+",
                "pub_date": "Sat, 17 Oct 2026 00:00:00 GMT",
                "news_items": [
                    {"headline": "Pemerintah Tingkatkan Insentif Guru", "source": "BorneoFlash.com", "url": "https://borneoflash.com/1"}
                ]
            }
        ]
        response = client.get("/api/v1/trends/daily?geo=ID")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["geo"] == "ID"
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Insentif Guru PAUD Samarinda"


def test_trends_autocomplete():
    """Menguji Google Autocomplete endpoint (GET /autocomplete?q=...)"""
    with patch("app.routers.trends.fetch_google_autocomplete") as mock_auto:
        mock_auto.return_value = [
            "insentif guru paud balikpapan",
            "insentif guru paud samarinda",
            "insentif guru paud kaltim 2026"
        ]
        response = client.get("/api/v1/trends/autocomplete?q=insentif+guru+paud&geo=ID")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total"] == 3
        assert "insentif guru paud balikpapan" in data["suggestions"]


def test_trends_questions():
    """Menguji People Also Ask (5W+1H) (GET /questions?keyword=...)"""
    with patch("app.routers.trends.fetch_people_also_ask") as mock_paa:
        mock_paa.return_value = [
            "Berapa insentif guru paud samarinda?",
            "Kapan insentif guru paud cair?",
            "Bagaimana syarat penerima insentif guru paud?"
        ]
        response = client.get("/api/v1/trends/questions?keyword=insentif+guru+paud&geo=ID")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total"] == 3


def test_trends_compare():
    """Menguji perbandingan tren kata kunci (POST /compare)"""
    payload = {
        "keywords": ["insentif guru", "gaji p3k guru"],
        "geo": "ID"
    }
    response = client.post("/api/v1/trends/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "keywords_data" in data
    assert "recommended_keyword" in data
    assert len(data["keywords_data"]) == 2


def test_indexing_status():
    """Menguji status kesiapan Google Instant Indexing API"""
    response = client.get("/api/v1/indexing/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data


def test_indexing_notify_mock():
    """Menguji pengiriman notifikasi Indexing dengan mock service"""
    with patch("app.routers.indexing.send_google_indexing_notification") as mock_send:
        mock_send.return_value = {
            "status": "success",
            "url": "https://borneoflash.com/berita-baru-hari-ini",
            "action": "URL_UPDATED",
            "notified_at": "2026-10-17T05:00:00Z"
        }
        payload = {
            "url": "https://borneoflash.com/berita-baru-hari-ini",
            "action": "URL_UPDATED"
        }
        response = client.post("/api/v1/indexing/notify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["url"] == "https://borneoflash.com/berita-baru-hari-ini"


def test_gsc_status():
    """Menguji endpoint status GSC"""
    response = client.get("/api/v1/gsc/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data


def test_cannibalization_audit():
    """Menguji audit kanibalisasi kata kunci antar artikel"""
    payload = {
        "articles": [
            {
                "id": "1",
                "title": "Pemerintah Berikan Insentif Guru PAUD di Balikpapan",
                "focus_keyword": "insentif guru paud balikpapan",
                "url": "https://borneoflash.com/artikel-1"
            },
            {
                "id": "2",
                "title": "Kabar Gembira: Insentif Guru PAUD Balikpapan Segera Cair",
                "focus_keyword": "insentif guru paud balikpapan",
                "url": "https://borneoflash.com/artikel-2"
            },
            {
                "id": "3",
                "title": "Pembangunan Jalan Tol IKN Terus Dikebut OIKN",
                "focus_keyword": "tol ikn nusantara",
                "url": "https://borneoflash.com/artikel-3"
            }
        ]
    }
    response = client.post("/api/v1/audit/cannibalization", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["clash_detected_count"] >= 1
    assert len(data["cannibalization_risks"]) >= 1
    assert data["cannibalization_risks"][0]["severity"] in ("Kritis", "Tinggi", "Sedang")
