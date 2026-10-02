from fastapi import FastAPI
from app.routers import seo

app = FastAPI(
    title="BorneoFlash SEO Engine Microservice",
    description="Engine analisis SEO Teknis & GEO berbasis PySastrawi dan 9Router AI",
    version="2.2.0"
)

# Include routers
app.include_router(seo.router)


@app.get("/")
def read_root():
    return {"status": "online", "service": "BorneoFlash SEO Engine Microservice", "version": "2.2.0"}


@app.get("/health")
def health_check():
    return {"status": "ok", "components": {"pysastrawi": "ready", "fastapi": "ready", "newspaper4k": "ready"}}
