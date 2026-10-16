import os
import glob
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

INDEXING_SCOPE = ["https://www.googleapis.com/auth/indexing"]
INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"


def find_service_account_file() -> Optional[str]:
    """Mencari file kredensial Google Service Account JSON dari .env atau folder lokal."""
    env_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if env_path and os.path.exists(env_path):
        return env_path

    # Cari kandidat file json di folder python/ atau root project
    search_paths = [
        os.path.join(os.getcwd(), "python", "*.json"),
        os.path.join(os.getcwd(), "..", "python", "*.json"),
        os.path.join("c:\\laragon\\www\\borneoflash\\python", "*.json"),
        os.path.join(os.getcwd(), "*.json")
    ]

    for p in search_paths:
        matches = glob.glob(p)
        for m in matches:
            if "analytics" in m.lower() or "indexing" in m.lower() or "borneoflash" in m.lower():
                return m

    return None


def get_indexing_credentials():
    """Membuat kredensial Google OAuth2 dengan scope Google Indexing API."""
    key_file = find_service_account_file()
    if not key_file:
        return None, "File Google Service Account JSON tidak ditemukan. Atur GOOGLE_SERVICE_ACCOUNT_JSON di file .env."

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        creds = service_account.Credentials.from_service_account_file(
            key_file, scopes=INDEXING_SCOPE
        )
        creds.refresh(Request())
        return creds, None
    except Exception as e:
        logger.error(f"Gagal memuat Google Credentials ({key_file}): {str(e)}")
        return None, f"Kredensial Google Service Account gagal diinisialisasi: {str(e)}"


def check_indexing_credentials_status() -> Dict[str, Any]:
    """Memeriksa status kesiapan kredensial Google Indexing API."""
    key_file = find_service_account_file()
    if not key_file:
        return {
            "configured": False,
            "message": "File Google Service Account JSON belum dikonfigurasi. Atur GOOGLE_SERVICE_ACCOUNT_JSON di .env.",
            "service_account_email": None,
            "project_id": None
        }

    try:
        import json
        with open(key_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "configured": True,
            "key_file": os.path.basename(key_file),
            "service_account_email": data.get("client_email"),
            "project_id": data.get("project_id"),
            "message": "Google Service Account siap digunakan untuk Instant Indexing API."
        }
    except Exception as e:
        return {
            "configured": False,
            "message": f"Error membaca file kredensial: {str(e)}",
            "service_account_email": None,
            "project_id": None
        }


def send_google_indexing_notification(url: str, action: str = "URL_UPDATED") -> Dict[str, Any]:
    """Mengirim notifikasi instan ke Google Indexing API agar Googlebot segera meng-crawl URL berita ini.
    
    Aksi valid: 'URL_UPDATED' (artikel baru/update) atau 'URL_DELETED' (artikel dihapus).
    """
    clean_url = url.strip()
    if not clean_url:
        return {"status": "error", "message": "URL tidak boleh kosong."}

    action_type = "URL_DELETED" if "delete" in action.lower() else "URL_UPDATED"
    creds, err = get_indexing_credentials()

    if not creds:
        return {
            "status": "unconfigured",
            "url": clean_url,
            "action": action_type,
            "message": err,
            "hint": "Tambahkan file service account JSON di .env (GOOGLE_SERVICE_ACCOUNT_JSON=...)"
        }

    try:
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }
        body = {
            "url": clean_url,
            "type": action_type
        }

        response = requests.post(INDEXING_ENDPOINT, headers=headers, json=body, timeout=10)
        resp_json = response.json() if response.content else {}

        if response.status_code in (200, 204):
            return {
                "status": "success",
                "url": clean_url,
                "action": action_type,
                "notify_time": datetime.now().isoformat(),
                "google_response": resp_json,
                "message": "Notifikasi instan berhasil dikirim ke Google Indexing API. Googlebot akan segera merayapi artikel ini."
            }
        else:
            return {
                "status": "error",
                "code": response.status_code,
                "url": clean_url,
                "action": action_type,
                "google_response": resp_json,
                "message": f"Google Indexing API mengembalikan kode HTTP {response.status_code}."
            }
    except Exception as e:
        logger.error(f"Gagal mengirim indexing notification untuk {clean_url}: {str(e)}")
        return {
            "status": "error",
            "url": clean_url,
            "action": action_type,
            "message": f"Gagal menghubungi Google Indexing API: {str(e)}"
        }


def batch_google_indexing_notifications(urls: List[str], action: str = "URL_UPDATED") -> Dict[str, Any]:
    """Mengirim serentak notifikasi Google Instant Indexing untuk beberapa URL berita."""
    results = []
    success_count = 0

    for u in urls:
        res = send_google_indexing_notification(u, action=action)
        results.append(res)
        if res.get("status") == "success":
            success_count += 1

    return {
        "status": "success" if success_count > 0 else "completed",
        "total": len(urls),
        "success_count": success_count,
        "failed_count": len(urls) - success_count,
        "items": results
    }
