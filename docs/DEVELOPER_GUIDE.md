# BorneoFlash SEO Engine — Developer Guide

> **Version:** 2.0.0
> **Stack:** Python 3.10+, FastAPI, PySastrawi, newspaper4k, BeautifulSoup4, 9Router AI

---

## Daftar Isi

1. [Quick Start](#quick-start)
2. [Struktur Proyek](#struktur-proyek)
3. [Konfigurasi](#konfigurasi)
4. [Arsitektur & Alur Data](#arsitektur--alur-data)
5. [Panduan Pengembangan](#panduan-pengembangan)
6. [Konvensi Kode](#konvensi-kode)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prasyarat

- **Python 3.10+** terinstal di sistem
- **9Router AI Proxy Gateway** (opsional, untuk analisis GEO/E-E-A-T)

### Instalasi

```bash
# 1. Clone / masuk ke folder proyek
cd C:\laragon\www\SEOEngine

# 2. Buat virtual environment (jika belum ada)
py -3.10 -m venv .venv

# 3. Aktifkan virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# 4. Install dependensi dari requirements.txt
pip install -r requirements.txt

# 5. Konfigurasi environment
cp .env.example .env
# Edit .env, isi NINEROUTER_API_KEY

# 6. Jalankan server development
python main.py
```

Server berjalan di **http://localhost:8000**
Swagger UI: **http://localhost:8000/docs**
ReDoc: **http://localhost:8000/redoc**

### Verifikasi Instalasi

```bash
# Health check
curl http://localhost:8000/health

# Seharusnya mengembalikan:
# {"status":"ok","components":{"pysastrawi":"ready","fastapi":"ready","newspaper4k":"ready"}}
```

---

## Struktur Proyek

```
SEOEngine/
├── main.py                          # Entry point — re-export app, uvicorn.run()
├── requirements.txt                 # Dependensi Python
├── .env.example                     # Template environment variables
├── .env                             # Konfigurasi aktif (git-ignored)
├── .gitignore
├── app/
│   ├── __init__.py                  # Package marker
│   ├── main.py                      # FastAPI() init, include_router, root & health endpoints
│   ├── routers/
│   │   ├── __init__.py
│   │   └── seo.py                   # 3 endpoint: analyze, analyze-url, schema-jsonld
│   ├── services/
│   │   ├── __init__.py
│   │   ├── technical_service.py     # PySastrawi stemmer, keyword density, skor teknis
│   │   ├── html_service.py          # BeautifulSoup: heading, image alt, link audit
│   │   ├── ninerouter_service.py    # HTTP call ke 9Router AI untuk GEO & E-E-A-T
│   │   └── schema_service.py        # Generator NewsArticle JSON-LD
│   └── schemas/
│       ├── __init__.py
│       └── seo_schema.py            # Pydantic models: ArticleAnalysisRequest, dll.
├── docs/
│   ├── API_REFERENCE.md             # Referensi API lengkap
│   ├── DEVELOPER_GUIDE.md           # Panduan pengembang (file ini)
│   ├── ARCHITECTURE.md              # Arsitektur sistem & keputusan desain
│   └── CHANGELOG.md                 # Riwayat perubahan
└── external_repos/                  # Repositori referensi (read-only, tidak dimodifikasi)
    ├── PySastrawi/                  # Indonesian stemmer library
    ├── crawl4ai/                    # Web crawling (referensi)
    ├── extruct/                     # Structured data extraction (referensi)
    ├── geo-seo-claude/              # GEO SEO patterns (referensi)
    ├── newspaper4k/                 # Article scraping library
    └── python-seo-analyzer/         # SEO analysis patterns (referensi)
```

### Penjelasan Modul

| File | Tanggung Jawab |
|---|---|
| `main.py` (root) | Entry point. Re-export `app` dari `app.main` agar uvicorn reloader bekerja. Menjalankan `uvicorn.run()` |
| `app/main.py` | Inisialisasi `FastAPI()`, mount router via `include_router()`, endpoint `/` dan `/health` |
| `app/routers/seo.py` | 3 endpoint POST: `/analyze`, `/analyze-url`, `/schema-jsonld`. Orkestrasi pemanggilan services |
| `app/services/technical_service.py` | Stemming via PySastrawi, keyword density calculation, skor teknis SEO, pengecekan 5W1H |
| `app/services/html_service.py` | Parse HTML via BeautifulSoup: audit heading H2/H3, image alt text, internal/external link |
| `app/services/ninerouter_service.py` | HTTP POST ke 9Router AI untuk evaluasi kualitatif GEO & E-E-A-T. Graceful fallback jika gagal |
| `app/services/schema_service.py` | Generate `NewsArticle` Schema.org JSON-LD dan render ke HTML snippet `<script>` |
| `app/schemas/seo_schema.py` | Pydantic models: `ArticleAnalysisRequest`, `URLAnalysisRequest`, `SchemaJSONLDRequest` |

---

## Konfigurasi

### Environment Variables

Konfigurasi disimpan di file `.env` (di-load via `python-dotenv`):

| Variabel | Deskripsi | Contoh |
|---|---|---|
| `NINEROUTER_URL` | Endpoint API 9Router (OpenAI-compatible) | `http://localhost:20128/v1/chat/completions` |
| `NINEROUTER_API_KEY` | API key untuk autentikasi 9Router | `sk-xxxxx` |

Variabel dibaca di `app/services/ninerouter_service.py`:

```python
load_dotenv()
NINEROUTER_URL = os.getenv("NINEROUTER_URL", "http://localhost:20128/v1/chat/completions")
NINEROUTER_API_KEY = os.getenv("NINEROUTER_API_KEY", "")
```

### 9Router AI Model

Model default yang digunakan: `ag/gemini-pro-agent`. Dikonfigurasi di payload request ke 9Router:

```python
payload = {
    "model": "ag/gemini-pro-agent",  # 9Router mengarahkan ke LLM aktif
    "messages": [...],
    "temperature": 0.2,
    "stream": False
}
```

### Stopwords Indonesia

Didefinisikan di `app/services/technical_service.py`:

```python
STOPWORDS_ID = {"di", "ke", "dari", "dan", "atau", "yang", "untuk", "dengan", "pada", "dalam", "oleh", "ini", "itu", "se", "ter"}
```

Digunakan untuk mencocokkan keyword di judul — kata hubung diabaikan, urutan bebas.

---

## Arsitektur & Alur Data

> Detail lengkap: [ARCHITECTURE.md](./ARCHITECTURE.md)

### POST /api/v1/seo/analyze — Alur Data

```
Request Body (JSON)
     │
     ├──► technical_service.analyze_technical_seo()
     │       ├── clean_text() → strip HTML, lowercase
     │       ├── stemmer.stem() via PySastrawi
     │       ├── Keyword density: (stemmed_count / total_words) × 100
     │       ├── Keyword-in-title check (stopword-aware, order-independent)
     │       ├── 5W1H detection
     │       └── Scoring: 100 - penalties → seo_score
     │
     ├──► html_service.analyze_html_structure()
     │       ├── BeautifulSoup parse
     │       ├── H2/H3 heading audit + keyword presence check
     │       ├── Image alt text audit (report missing)
     │       └── Internal/External link audit + domain extraction
     │
     └──► ninerouter_service.call_9router_for_geo()  [jika use_ai_analysis=true]
             ├── Compose prompt → POST ke 9Router
             ├── Parse JSON response → eeat_score, per-component scores
             └── Graceful fallback: semua skor 0 jika gagal
     │
     ▼
Aggregate:
  - overall_score = (seo_score × 0.6) + (eeat_score × 0.4)
  - combined_suggestions = deduplicated, order-preserving merge
```

### POST /api/v1/seo/analyze-url — Alur Data

```
URL Input
     │
     ├──► newspaper4k: Article.download() → Article.parse()
     │       └── Extract: title, text, html, authors, publish_date, top_image
     │
     ├──► Truncate text ke 3000 karakter (untuk prompt AI)
     │
     └──► Pipeline yang sama dengan /analyze
             + url_metadata dalam response
```

---

## Panduan Pengembangan

### Menambah Service Baru

1. Buat file `app/services/nama_service.py`
2. Definisikan fungsi-fungsi logika bisnis dengan type hints
3. Import dan panggil dari `app/routers/seo.py`

```python
# app/services/nama_service.py
from typing import Dict, Any

def process_something(data: str) -> Dict[str, Any]:
    """Deskripsi fungsi dalam Bahasa Indonesia."""
    # logika bisnis
    return {"result": "..."}
```

### Menambah Endpoint Baru

1. Tambahkan Pydantic model di `app/schemas/seo_schema.py`
2. Tambahkan handler di `app/routers/seo.py`
3. Test via Swagger UI (`/docs`)

```python
# 1. Di seo_schema.py
class NewFeatureRequest(BaseModel):
    field1: str = Field(..., examples=["contoh"])
    field2: Optional[int] = None

# 2. Di seo.py
@router.post("/new-feature")
def new_feature(payload: NewFeatureRequest):
    """Deskripsi endpoint."""
    result = some_service_function(payload.field1)
    return {"status": "success", "data": result}
```

### Menambah Router Baru

1. Buat file `app/routers/nama_router.py`
2. Definisikan `router = APIRouter(prefix="/api/v1/...", tags=[...])`
3. Import dan `app.include_router()` di `app/main.py`

```python
# app/routers/content.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/content", tags=["Content"])

@router.get("/stats")
def get_stats():
    return {"status": "success", "data": {...}}
```

```python
# app/main.py — tambahkan:
from app.routers import content
app.include_router(content.router)
```

---

## Konvensi Kode

### Umum

- **Bahasa**: Komentar, docstring, dan pesan error dalam **Bahasa Indonesia**
- **Type hints**: Semua fungsi harus punya type hints (parameter dan return)
- **Docstring**: Wajib untuk setiap fungsi publik

### Response Format

Semua endpoint mengembalikan format konsisten:

```python
# Sukses
{"status": "success", "data": {...}, "provider": "fastapi"}

# Error (via HTTPException)
{"detail": "Pesan error deskriptif"}
```

### Error Handling

- Gunakan `HTTPException` untuk error yang ditujukan ke client
- Service yang memanggil external API (9Router) harus punya **graceful fallback**
- Jangan biarkan exception internal bocor ke response

### Suggestions Pattern

Gabungkan saran dari semua service, deduplicate dengan `dict.fromkeys()` untuk menjaga urutan:

```python
all_suggestions = technical_res.get("technical_suggestions", [])[:]
all_suggestions.extend(html_res.get("html_suggestions", []))
# ... extend dari geo_res
all_suggestions = list(dict.fromkeys(all_suggestions))
```

### Dependencies

Dependensi tercatat di `requirements.txt`. Saat menambah library baru:

```bash
pip install nama-library
pip freeze | findstr nama-library >> requirements.txt
# Atau edit requirements.txt secara manual
```

---

## Troubleshooting

### Server Tidak Bisa Start

| Gejala | Penyebab | Solusi |
|---|---|---|
| `ModuleNotFoundError: No module named 'Sastrawi'` | PySastrawi belum terinstal | `pip install PySastrawi` |
| `ModuleNotFoundError: No module named 'fastapi'` | Virtual env belum aktif | Aktifkan `.venv` dulu |
| Port 8000 already in use | Proses lain pakai port 8000 | Kill proses atau ganti port: `uvicorn app.main:app --port 8001` |

### 9Router AI Tidak Merespon

| Gejala | Penyebab | Solusi |
|---|---|---|
| E-E-A-T skor semua 0 | 9Router offline atau API key salah | Cek `.env`, pastikan `NINEROUTER_URL` dan `NINEROUTER_API_KEY` benar |
| Timeout error | 9Router terlalu lama merespon | Timeout default 30 detik. Pastikan model tersedia di 9Router |
| `use_ai_analysis: false` | Sengaja dimatikan | E-E-A-T dilewati, `overall_score = seo_score` |

### newspaper4k Gagal Scrape

| Gejala | Penyebab | Solusi |
|---|---|---|
| HTTP 400: "Gagal mengambil artikel" | URL tidak valid, server target blocking | Pastikan URL bisa diakses, coba buka manual dulu |
| HTTP 400: "Tidak ada konten teks" | Halaman JS-rendered / paywall | newspaper4k tidak bisa render JavaScript |
| HTTP 500: "Library newspaper4k belum terinstal" | newspaper4k belum di-install | `pip install newspaper4k lxml` |

### Menjalankan untuk Development

```bash
# Cara 1: via entry point (auto-reload enabled)
python main.py

# Cara 2: via uvicorn langsung (lebih fleksibel)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Cara 3: production (gunicorn + uvicorn worker)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Tips Debug

- **Swagger UI**: `http://localhost:8000/docs` — test semua endpoint interaktif
- **ReDoc**: `http://localhost:8000/redoc` — dokumentasi API read-only
- **Skip AI**: Set `use_ai_analysis: false` di request untuk skip analisis GEO saat 9Router offline
- **Logs**: Uvicorn mencetak request/response ke stdout. Gunakan `--log-level debug` untuk detail
