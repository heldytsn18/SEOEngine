import os
import logging
from fastapi import FastAPI, Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.routers import seo

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
    title="BorneoFlash SEO Engine Microservice",
    description="Engine analisis SEO Teknis & GEO berbasis PySastrawi dan 9Router AI",
    version="2.2.0",
    dependencies=[Security(verify_api_key)]
)

# Include routers
app.include_router(seo.router)


@app.get("/")
def read_root():
    return {"status": "online", "service": "BorneoFlash SEO Engine Microservice", "version": "2.2.0"}


@app.get("/health")
def health_check():
    return {"status": "ok", "components": {"pysastrawi": "ready", "fastapi": "ready", "newspaper4k": "ready"}}
