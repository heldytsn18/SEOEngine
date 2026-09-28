# 🔍 BorneoFlash SEO Engine Microservice

> **Engine analisis SEO Teknis & GEO berbasis PySastrawi dan 9Router AI**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: Proprietary](https://img.shields.io/badge/license-proprietary-red.svg)](#)

---

## 📋 Deskripsi

**BorneoFlash SEO Engine** adalah microservice REST API yang dirancang khusus untuk analisis SEO artikel berita berbahasa Indonesia. Engine ini menggabungkan:

- **Analisis Teknis Lokal** — Keyword density, headline scoring, dan readability menggunakan **PySastrawi** (Indonesian stemmer)
- **Audit Struktur HTML** — Inspeksi heading tags (H2/H3), image alt text, dan link audit menggunakan **BeautifulSoup4**
- **Evaluasi GEO & E-E-A-T** — Penilaian kualitatif via **9Router AI Proxy Gateway** (opsional)
- **Schema.org JSON-LD Generator** — Generate `NewsArticle` structured data yang valid untuk Google News
- **Scraping Artikel Kompetitor** — Ekstrak dan analisis URL artikel menggunakan **newspaper4k**

---

## ⚡ Quick Start

### Prasyarat

- Python 3.10+
- 9Router AI Proxy Gateway (opsional, untuk fitur GEO/E-E-A-T)

### Instalasi

```bash
# 1. Clone / masuk ke folder proyek
cd SEOEngine

# 2. Buat virtual environment
py -3.10 -m venv .venv

# 3. Aktifkan virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 4. Install dependensi
pip install -r requirements.txt

# 5. Konfigurasi environment
cp .env.example .env
# Edit .env → isi NINEROUTER_API_KEY dengan key dari dasbor 9Router

# 6. Jalankan server
python main.py
```

Server berjalan di **http://localhost:8000**
Swagger UI: **http://localhost:8000/docs**
ReDoc: **http://localhost:8000/redoc**

---

## 🏗️ Arsitektur

```
Client Request
     │
     ▼
┌─────────────────────────────────────────────┐
│              FastAPI Application             │
│  app/main.py — mount router, health check   │
├─────────────────────────────────────────────┤
│              Router Layer                    │
│  app/routers/seo.py — 3 endpoint POST       │
├───────────┬───────────┬─────────────────────┤
│ Technical │   HTML    │   NineRouter        │
│ Service   │  Service  │   Service           │
│ PySastrawi│ BS4 parse │   9Router AI call   │
├───────────┴───────────┴─────────────────────┤
│              Schema Service                  │
│  NewsArticle JSON-LD generator              │
└─────────────────────────────────────────────┘
```

---

## 📡 API Endpoints

| Endpoint | Method | Deskripsi |
|---|---|---|
| `/` | GET | Status server |
| `/health` | GET | Health check komponen |
| `/api/v1/seo/analyze` | POST | Analisis draf artikel (teknis + HTML + GEO) |
| `/api/v1/seo/analyze-url` | POST | Scrape & analisis URL kompetitor |
| `/api/v1/seo/schema-jsonld` | POST | Generate NewsArticle JSON-LD |

> 📖 Detail lengkap: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## 📁 Struktur Proyek

```
SEOEngine/
├── main.py                          # Entry point (python main.py)
├── requirements.txt                 # Dependensi Python
├── .env.example                     # Template konfigurasi environment
├── .env                             # Konfigurasi aktif (git-ignored)
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py                      # Inisialisasi FastAPI + include_router
│   ├── routers/
│   │   ├── __init__.py
│   │   └── seo.py                   # Semua endpoint SEO (/api/v1/seo/*)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── technical_service.py     # PySastrawi stemmer, keyword density, scoring
│   │   ├── html_service.py          # Heading audit, image alt, link audit
│   │   ├── ninerouter_service.py    # Integrasi 9Router AI Proxy
│   │   └── schema_service.py        # Generator NewsArticle JSON-LD
│   └── schemas/
│       ├── __init__.py
│       └── seo_schema.py            # Pydantic request models
├── docs/
│   ├── API_REFERENCE.md             # Referensi API lengkap
│   ├── DEVELOPER_GUIDE.md           # Panduan pengembang
│   ├── ARCHITECTURE.md              # Arsitektur & alur data
│   ├── DEPLOYMENT.md                # Panduan deployment VPS, Docker
│   └── CHANGELOG.md                 # Riwayat perubahan
└── external_repos/                  # Repositori referensi (read-only)
    ├── PySastrawi/
    ├── crawl4ai/
    ├── extruct/
    ├── geo-seo-claude/
    ├── newspaper4k/
    └── python-seo-analyzer/
```

---

## 🔧 Konfigurasi

Konfigurasi menggunakan file `.env`. Salin dari `.env.example`:

| Variabel | Deskripsi | Default |
|---|---|---|
| `NINEROUTER_URL` | Endpoint API 9Router (OpenAI-compatible) | `https://api.ninerouter.com/v1/chat/completions` |
| `NINEROUTER_API_KEY` | API key untuk autentikasi 9Router | — (wajib diisi) |

---

## 🧪 Pengujian Cepat

Setelah server berjalan, test via `curl`:

```bash
# Health check
curl http://localhost:8000/health

# Analisis artikel (tanpa AI)
curl -X POST http://localhost:8000/api/v1/seo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Polri Tindak Lanjut Judi Online di Kaltim",
    "content": "Kepolisian Daerah Kalimantan Timur melakukan tindakan tegas terhadap pelaku judi online di wilayah Balikpapan dan Samarinda.",
    "focus_keyword": "Judi Online Kaltim",
    "use_ai_analysis": false
  }'
```

Atau gunakan Swagger UI di **http://localhost:8000/docs** untuk testing interaktif.

---

## 📖 Dokumentasi

| Dokumen | Deskripsi |
|---|---|
| [API Reference](docs/API_REFERENCE.md) | Spesifikasi lengkap semua endpoint, request/response |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Panduan setup, pengembangan, dan konvensi kode |
| [Architecture](docs/ARCHITECTURE.md) | Arsitektur sistem, alur data, dan keputusan desain |
| [Deployment Guide](docs/DEPLOYMENT.md) | Panduan deployment VPS, systemd, Nginx, Docker |
| [Changelog](docs/CHANGELOG.md) | Riwayat perubahan per versi |

---

## 🚀 Deployment

### Development

```bash
python main.py
# atau
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (VPS)

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

> 📖 Panduan lengkap (systemd, Nginx, Docker): [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 🛠️ Tech Stack

| Komponen | Teknologi | Fungsi |
|---|---|---|
| Framework | FastAPI | REST API framework |
| Stemmer | PySastrawi | Indonesian word stemming |
| HTML Parser | BeautifulSoup4 + lxml | Parsing & audit struktur HTML |
| Scraper | newspaper4k | Ekstraksi artikel dari URL |
| AI Proxy | 9Router | LLM gateway untuk evaluasi GEO/E-E-A-T |
| Validation | Pydantic | Request/response schema validation |
| Server | Uvicorn | ASGI server |
| Config | python-dotenv | Environment variable management |

---

## 📄 Lisensi

Proprietary — BorneoFlash Media. Hak cipta dilindungi.
