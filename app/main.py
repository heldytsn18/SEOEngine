import os
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.routers import seo, trends, indexing, gsc, audit
from app.services.indexing_service import check_indexing_credentials_status
from app.services.gsc_service import check_gsc_credentials_status

# Structured logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# API Key auth
SEO_API_KEY = os.getenv("SEO_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Validasi X-API-Key header jika SEO_API_KEY dikonfigurasi di .env."""
    if not SEO_API_KEY:
        return  # Auth disabled jika key belum di-set
    if api_key != SEO_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key tidak valid atau tidak disertakan. Sertakan header X-API-Key."
        )


app = FastAPI(
    title="BorneoFlash SEO & News Intelligence Engine",
    description="Engine analisis SEO Teknis, GEO AI 9Router, Google Trends, Instant Indexing & Search Console Analytics",
    version="3.0.0",
    dependencies=[Security(verify_api_key)]
)

# Include v3.0 routers
app.include_router(seo.router)
app.include_router(trends.router)
app.include_router(indexing.router)
app.include_router(gsc.router)
app.include_router(audit.router)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "BorneoFlash SEO & News Intelligence Engine",
        "version": "3.0.0",
        "modules": [
            "Technical SEO & Readability",
            "GEO & E-E-A-T AI (9Router)",
            "Google Trends Realtime & Autocomplete",
            "Google Instant Indexing API",
            "Google Search Console Performance",
            "Keyword Cannibalization Audit"
        ]
    }


@app.get("/health")
def health_check():
    idx_status = check_indexing_credentials_status()
    gsc_status = check_gsc_credentials_status()
    return {
        "status": "ok",
        "version": "3.0.0",
        "components": {
            "fastapi": "ready",
            "pysastrawi": "ready",
            "newspaper4k": "ready",
            "google_trends": "ready",
            "google_indexing_api": "ready" if idx_status.get("configured") else "unconfigured (needs JSON key in .env)",
            "google_search_console": "ready" if gsc_status.get("configured") else "unconfigured (needs JSON key in .env)"
        }
    }
