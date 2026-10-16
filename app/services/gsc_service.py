import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
import urllib.parse

from app.services.indexing_service import find_service_account_file

logger = logging.getLogger(__name__)

GSC_READONLY_SCOPE = ["https://www.googleapis.com/auth/webmasters.readonly"]
GSC_DEFAULT_SITE_URL = os.getenv("GSC_SITE_URL", "sc-domain:borneoflash.com")


def get_gsc_credentials():
    """Membuat kredensial OAuth2 untuk Google Search Console API."""
    key_file = find_service_account_file()
    if not key_file:
        return None, "File Google Service Account JSON tidak ditemukan. Atur GOOGLE_SERVICE_ACCOUNT_JSON di file .env."

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        creds = service_account.Credentials.from_service_account_file(
            key_file, scopes=GSC_READONLY_SCOPE
        )
        creds.refresh(Request())
        return creds, None
    except Exception as e:
        logger.error(f"Gagal memuat GSC Credentials ({key_file}): {str(e)}")
        return None, f"Kredensial Google Search Console gagal diinisialisasi: {str(e)}"


def check_gsc_credentials_status() -> Dict[str, Any]:
    """Memeriksa kesiapan konfigurasi Google Search Console API."""
    key_file = find_service_account_file()
    if not key_file:
        return {
            "configured": False,
            "site_url": GSC_DEFAULT_SITE_URL,
            "message": "File service account JSON belum di-set di .env.",
            "service_account_email": None
        }

    try:
        import json
        with open(key_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        email = data.get("client_email")
        return {
            "configured": True,
            "site_url": GSC_DEFAULT_SITE_URL,
            "service_account_email": email,
            "message": "Service account siap. Pastikan email ini telah ditambahkan sebagai 'Pengguna/Pemilik Penuh' pada properti Google Search Console Anda (borneoflash.com)."
        }
    except Exception as e:
        return {
            "configured": False,
            "site_url": GSC_DEFAULT_SITE_URL,
            "message": f"Error: {str(e)}",
            "service_account_email": None
        }


def get_gsc_url_performance(url: str, days: int = 28, site_url: Optional[str] = None) -> Dict[str, Any]:
    """Mengambil performa klik, tayangan, CTR, dan posisi ranking Google untuk URL spesifik."""
    clean_url = url.strip()
    target_site = site_url.strip() if site_url else GSC_DEFAULT_SITE_URL

    creds, err = get_gsc_credentials()
    if not creds:
        return {
            "status": "unconfigured",
            "url": clean_url,
            "message": err,
            "metrics": {
                "clicks": 0,
                "impressions": 0,
                "ctr": 0.0,
                "position": 0.0,
                "queries": []
            }
        }

    end_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days + 2)).strftime("%Y-%m-%d")

    encoded_site = urllib.parse.quote_plus(target_site)
    api_url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["query"],
        "dimensionFilterGroups": [
            {
                "filters": [
                    {
                        "dimension": "page",
                        "operator": "equals",
                        "expression": clean_url
                    }
                ]
            }
        ],
        "rowLimit": 15
    }

    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            rows = data.get("rows", [])
            total_clicks = sum(r.get("clicks", 0) for r in rows)
            total_impressions = sum(r.get("impressions", 0) for r in rows)
            avg_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0.0
            avg_position = round(sum(r.get("position", 0) for r in rows) / len(rows), 1) if rows else 0.0

            top_queries = [
                {
                    "query": r.get("keys", [""])[0],
                    "clicks": r.get("clicks", 0),
                    "impressions": r.get("impressions", 0),
                    "ctr": round(r.get("ctr", 0) * 100, 2),
                    "position": round(r.get("position", 0), 1)
                }
                for r in rows
            ]

            return {
                "status": "success",
                "url": clean_url,
                "date_range": f"{start_date} s/d {end_date}",
                "metrics": {
                    "clicks": total_clicks,
                    "impressions": total_impressions,
                    "ctr_percent": avg_ctr,
                    "avg_position": avg_position,
                    "queries_count": len(rows),
                    "top_queries": top_queries
                }
            }
        else:
            return {
                "status": "error",
                "code": resp.status_code,
                "url": clean_url,
                "message": f"GSC API error (HTTP {resp.status_code}): {resp.text}"
            }
    except Exception as e:
        logger.error(f"Gagal mengambil metrik GSC untuk {clean_url}: {str(e)}")
        return {
            "status": "error",
            "url": clean_url,
            "message": f"Error koneksi GSC: {str(e)}"
        }


def get_gsc_low_hanging_fruits(
    site_url: Optional[str] = None,
    days: int = 28,
    min_impressions: int = 100,
    max_ctr: float = 0.05
) -> Dict[str, Any]:
    """Menemukan peluang optimasi emas (Low-Hanging Fruits):
    
    Kueri pencarian yang tayang tinggi di Google (impresi >= min_impressions) dengan ranking halaman 1-2 (posisi 3-20),
    namun CTR-nya masih rendah (< max_ctr). Cocok untuk diperbaiki judul dan meta description-nya agar klik melonjak!
    """
    target_site = site_url.strip() if site_url else GSC_DEFAULT_SITE_URL
    creds, err = get_gsc_credentials()

    if not creds:
        return {
            "status": "unconfigured",
            "site_url": target_site,
            "message": err,
            "opportunities": []
        }

    end_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days + 2)).strftime("%Y-%m-%d")

    encoded_site = urllib.parse.quote_plus(target_site)
    api_url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["query", "page"],
        "rowLimit": 500
    }

    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            rows = data.get("rows", [])
            opportunities = []

            for r in rows:
                keys = r.get("keys", ["", ""])
                query = keys[0] if len(keys) > 0 else ""
                page_url = keys[1] if len(keys) > 1 else ""
                impressions = r.get("impressions", 0)
                clicks = r.get("clicks", 0)
                ctr = r.get("ctr", 0.0)
                position = r.get("position", 0.0)

                # Syarat Low-Hanging Fruit: Impresi cukup banyak, posisi rangking 3-20, tapi CTR di bawah target
                if impressions >= min_impressions and ctr <= max_ctr and 3.0 <= position <= 20.0:
                    potential_gain = round(impressions * 0.10) - clicks  # Estimasi jika CTR naik ke 10%
                    opportunities.append({
                        "query": query,
                        "url": page_url,
                        "impressions": impressions,
                        "clicks": clicks,
                        "current_ctr_percent": round(ctr * 100, 2),
                        "avg_position": round(position, 1),
                        "potential_click_gain": max(0, potential_gain),
                        "recommendation": f"Perbarui judul & meta deskripsi halaman ini agar memuat kueri '{query}' untuk menarik klik Google."
                    })

            # Urutkan berdasarkan peluang klik terbesar
            opportunities.sort(key=lambda x: x["potential_click_gain"], reverse=True)

            return {
                "status": "success",
                "site_url": target_site,
                "total_opportunities": len(opportunities),
                "items": opportunities[:30]
            }
        else:
            return {
                "status": "error",
                "code": resp.status_code,
                "message": f"GSC API error (HTTP {resp.status_code}): {resp.text}"
            }
    except Exception as e:
        logger.error(f"Gagal mengambil peluang GSC: {str(e)}")
        return {
            "status": "error",
            "message": f"Error koneksi GSC: {str(e)}"
        }
