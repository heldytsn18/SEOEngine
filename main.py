"""
BorneoFlash SEO Engine Microservice - Entry Point
Jalankan: .venv/Scripts/python.exe main.py
Atau:     uvicorn app.main:app --reload
"""
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Re-export app agar uvicorn reloader bisa menemukan atribut "app"
# saat StatReload mendeteksi perubahan di main.py
from app.main import app  # noqa: F401

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)