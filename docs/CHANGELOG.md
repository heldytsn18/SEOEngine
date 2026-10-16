# Changelog

Semua perubahan penting pada BorneoFlash SEO Engine didokumentasikan di file ini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.0.0/).

## [3.0.0] — 2026-10-17

### Ditambahkan
- **Modul Google Trends & Search Demand Intelligence (`/api/v1/trends`)**:
  - `GET /api/v1/trends/daily`: Topik pencarian terhangat hari ini dari Google Trends RSS resmi (traffic, headline, rujukan berita).
  - `GET /api/v1/trends/autocomplete`: Saran kata kunci riil yang sedang aktif diketik pengguna di Google Search (Google Suggest API).
  - `GET /api/v1/trends/questions`: Pertanyaan populer publik di Google (People Also Ask) berbasis formula 5W+1H Indonesia.
  - `POST /api/v1/trends/compare`: Komparasi search demand & popularitas antara 2–5 kata kunci alternatif untuk penentuan kata kunci fokus terbaik.
- **Modul Google Instant Indexing API (`/api/v1/indexing`)**:
  - Integrasi resmi Google Indexing API v3 (`https://indexing.googleapis.com/v3/urlNotifications:publish`) via Google Service Account JSON.
  - `GET /api/v1/indexing/status`: Cek kesiapan service account JSON.
  - `POST /api/v1/indexing/notify`: Notifikasi instan URL_UPDATED atau URL_DELETED ke Googlebot agar artikel segera dirayapi (1–5 menit).
  - `POST /api/v1/indexing/batch`: Pengiriman batch notifikasi perayapan hingga 100 URL berita sekaligus.
- **Modul Google Search Console API (`/api/v1/gsc`)**:
  - `GET /api/v1/gsc/status`: Cek kesiapan kredensial GSC.
  - `POST /api/v1/gsc/url-performance`: Penarikan performa riil artikel (Clicks, Impressions, CTR, Position) langsung dari Google Search Console.
  - `POST /api/v1/gsc/opportunities`: Deteksi peluang emas *Low-Hanging Fruits* (kueri dengan impresi tinggi di halaman 1–2 Google tapi CTR masih rendah).
- **Modul Audit Kanibalisasi Kata Kunci (`/api/v1/audit`)**:
  - `POST /api/v1/audit/cannibalization`: Deteksi benturan kata kunci fokus dan judul serupa antar artikel portal berita BorneoFlash via Jaccard similarity word-level & exact keyword match.
- **Pengayaan Endpoint Eksisting**:
  - `/api/v1/seo/analyze` & `/api/v1/seo/check-score` kini otomatis mengembalikan `google_search_insights` (autocomplete queries & people-also-ask) langsung dari Google Search tanpa breaking changes.
- **Dependensi Baru**:
  - `google-auth` untuk autentikasi OAuth2 JWT Google Service Account.

### Diperbaiki
- Mengatasi shadowing modul bawaan Python `html` pada fungsi scraping/analisis URL.
- Memperbarui Pydantic validation field dari `min_items`/`max_items` ke `min_length`/`max_length` sesuai standar Pydantic v2.

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
