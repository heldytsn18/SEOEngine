"""
BorneoFlash SEO Engine Microservice - Entry Point
Jalankan: .venv/Scripts/python.exe main.py
Atau:     uvicorn app.main:app --reload
"""
import uvicorn

# Re-export app agar uvicorn reloader bisa menemukan atribut "app"
# saat StatReload mendeteksi perubahan di main.py
from app.main import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)