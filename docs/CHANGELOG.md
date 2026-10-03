# Changelog

Semua perubahan penting pada BorneoFlash SEO Engine didokumentasikan di file ini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.0.0/).

---

## [2.2.0] — 2026-10-03

### Ditambahkan
- **Endpoint `/api/v1/seo/improve-content`** — Auto-fix/perbaiki draf artikel berdasarkan evaluasi teknis SEO & keterbacaan, dengan perbandingan skor sebelum/sesudah
- **Improvement Service** (`improvement_service.py`) — Logika perbaikan konten via 9Router AI dengan fallback heuristik lokal
- **Structured Logging** — Seluruh service kini menggunakan `logging` module untuk tracing error & debugging
- **API Key Authentication** — Middleware autentikasi `X-API-Key` header untuk seluruh endpoint POST

### Diperbaiki
- Duplikasi `load_dotenv()` dihapus dari `ninerouter_service.py` (cukup dipanggil di entry point)

---

## [2.1.0] — 2026-09-30

### Ditambahkan
- **Endpoint `/api/v1/seo/analyze-taxonomy`** — Analisis SEO taksonomi berita (kategori, tag, topik khusus) via AI & heuristik lokal
- **Endpoint `/api/v1/seo/rewrite-url`** — Scrape artikel dari URL lalu tulis ulang menjadi naskah berita baru yang orisinal
- **Taxonomy Service** (`taxonomy_service.py`) — Analisis & generasi metadata SEO untuk halaman arsip taksonomi
- **Rewrite Service** (`rewrite_service.py`) — Penulisan ulang artikel via 9Router AI dengan anti-plagiarism Jaccard 3-gram check
- **Scraper Service** (`scraper_service.py`) — Scraping URL artikel dengan 4 User-Agent rotation, paginasi view-all detection, multi-selector extraction
- **Pydantic Models** — `TaxonomyAnalysisRequest`, `URLRewriteRequest`, `ContentImprovementRequest`

---

## [2.0.1] — 2026-09-29

### Dokumentasi
- **`docs/DEPLOYMENT.md`** — Panduan deployment lengkap: VPS, systemd, Nginx, Caddy, Docker
- **`docs/ARCHITECTURE.md`** — Tambah bagian Deployment, hapus dependensi `httpx` yang belum digunakan
- **`docs/DEVELOPER_GUIDE.md`** — Perbaiki URL default `NINEROUTER_URL` agar sesuai `.env.example`, tambah bagian Deployment (systemd, Nginx)
- **`docs/CHANGELOG.md`** — Riwayat perubahan per versi (file ini)
- **`README.md`** — Tambah bagian Deployment, link ke `DEPLOYMENT.md`, perbaiki tabel dokumentasi

---

## [2.0.0] — 2026-09-24

### Ditambahkan
- **Endpoint `/api/v1/seo/analyze`** — Analisis draf artikel: skor teknis SEO, struktur HTML, dan evaluasi GEO/E-E-A-T
- **Endpoint `/api/v1/seo/analyze-url`** — Scrape & analisis URL artikel kompetitor via newspaper4k
- **Endpoint `/api/v1/seo/schema-jsonld`** — Generator NewsArticle Schema.org JSON-LD untuk Google News
- **Technical Service** — Keyword density via PySastrawi stemmer, headline scoring, 5W1H detection
- **HTML Service** — Heading audit (H2/H3), image alt text audit, internal/external link audit via BeautifulSoup4
- **NineRouter Service** — Integrasi 9Router AI Proxy untuk evaluasi kualitatif GEO & E-E-A-T
- **Schema Service** — Generator `NewsArticle` JSON-LD dengan HTML snippet output
- **Hybrid Scoring** — Formula agregat: `(teknis × 0.6) + (E-E-A-T × 0.4)` dengan graceful fallback
- **Environment config** — Konfigurasi 9Router via `.env` file (python-dotenv)
- **Pydantic models** — `ArticleAnalysisRequest`, `URLAnalysisRequest`, `SchemaJSONLDRequest`
- **Suggestion deduplication** — Gabungan saran dari semua service, order-preserving, tanpa duplikat
- **Swagger UI & ReDoc** — Dokumentasi API interaktif otomatis dari FastAPI

### Dokumentasi
- `docs/API_REFERENCE.md` — Referensi API lengkap semua endpoint
- `docs/DEVELOPER_GUIDE.md` — Panduan setup, pengembangan, dan konvensi
- `docs/ARCHITECTURE.md` — Arsitektur sistem dan keputusan desain
- `docs/CHANGELOG.md` — Riwayat perubahan (file ini)
- `README.md` — Overview proyek dan quick start

### Dependensi
- FastAPI + Uvicorn (ASGI)
- PySastrawi (Indonesian stemmer)
- newspaper4k + lxml (article scraping)
- BeautifulSoup4 (HTML parsing)
- Pydantic (validation)
- requests (HTTP client)
- python-dotenv (env config)
- gunicorn (production server)

---

## [1.0.0] — 2026-09-20

### Ditambahkan
- Setup awal proyek SEO Engine
- Struktur folder `app/routers/`, `app/services/`, `app/schemas/`
- Integrasi awal PySastrawi untuk stemming bahasa Indonesia
