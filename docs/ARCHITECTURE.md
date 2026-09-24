# BorneoFlash SEO Engine — Architecture

> **Version:** 2.0.0
> **Terakhir diperbarui:** September 2026

---

## Daftar Isi

1. [Ringkasan Sistem](#ringkasan-sistem)
2. [Layer Architecture](#layer-architecture)
3. [Component Diagram](#component-diagram)
4. [Alur Data per Endpoint](#alur-data-per-endpoint)
5. [Service Details](#service-details)
6. [External Dependencies](#external-dependencies)
7. [Keputusan Desain](#keputusan-desain)
8. [Skalabilitas & Limitasi](#skalabilitas--limitasi)

---

## Ringkasan Sistem

BorneoFlash SEO Engine adalah **microservice REST API** yang menganalisis artikel berita berbahasa Indonesia dari perspektif SEO teknis, struktur HTML, dan kualitas konten (GEO/E-E-A-T).

Sistem menggabungkan **analisis lokal** (rule-based + NLP stemming) dengan **evaluasi AI** (via external LLM gateway) untuk menghasilkan skor komprehensif dan saran perbaikan.

### Prinsip Desain

- **Hybrid Analysis**: Kombinasi analisis deterministik lokal dan evaluasi AI probabilistik
- **Graceful Degradation**: Jika AI proxy (9Router) tidak tersedia, sistem tetap menghasilkan skor teknis
- **Single Responsibility**: Setiap service menangani satu domain analisis
- **Indonesian-First**: Stemmer, stopwords, dan prompt dioptimalkan untuk bahasa Indonesia

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT LAYER                       │
│          HTTP Client / Swagger UI / ReDoc            │
└────────────────────────┬────────────────────────────┘
                         │ HTTP Request (JSON)
                         ▼
┌─────────────────────────────────────────────────────┐
│                   FRAMEWORK LAYER                    │
│                                                      │
│   FastAPI Application  (app/main.py)                │
│   ├── CORS / Middleware (jika ditambah)              │
│   ├── Root endpoint: GET /                          │
│   └── Health endpoint: GET /health                  │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   ROUTER LAYER                       │
│                                                      │
│   app/routers/seo.py                                │
│   ├── POST /api/v1/seo/analyze                      │
│   ├── POST /api/v1/seo/analyze-url                  │
│   └── POST /api/v1/seo/schema-jsonld                │
│                                                      │
│   Tanggung jawab: Request validation, orchestration,│
│   aggregate scoring, response assembly              │
└────────────────────────┬────────────────────────────┘
                         │
          ┌──────────────┼──────────────┬──────────────┐
          ▼              ▼              ▼              ▼
┌───────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
│  Technical    │ │    HTML      │ │ NineRouter│ │  Schema  │
│  Service      │ │   Service    │ │  Service  │ │  Service │
│               │ │              │ │           │ │          │
│ PySastrawi    │ │ BeautifulSoup│ │ HTTP POST │ │ JSON-LD  │
│ Stemming      │ │ HTML Parsing │ │ to 9Router│ │ Generator│
│ Rule-based    │ │ Audit        │ │ AI Proxy  │ │          │
│ Scoring       │ │              │ │           │ │          │
└───────────────┘ └──────────────┘ └──────────┘ └──────────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  9Router AI  │
                                  │  Proxy GW    │
                                  │  (External)  │
                                  └──────────────┘
```

---

## Component Diagram

### Request Models (Schema Layer)

```
app/schemas/seo_schema.py
│
├── ArticleAnalysisRequest
│   ├── title: str (required)
│   ├── content: str (required)
│   ├── focus_keyword: str (required)
│   ├── category: Optional[str]
│   └── use_ai_analysis: Optional[bool] = True
│
├── URLAnalysisRequest
│   ├── url: str (required)
│   ├── focus_keyword: str (required)
│   └── use_ai_analysis: Optional[bool] = True
│
└── SchemaJSONLDRequest
    ├── title: str (required)
    ├── description: str (required)
    ├── author_name: str (required)
    ├── publisher_name: str (required)
    ├── publisher_logo_url: str (required)
    ├── date_published: str (required)
    ├── date_modified: Optional[str]
    ├── image_url: Optional[str]
    └── article_url: str (required)
```

### Service Interfaces

```
technical_service.py
├── clean_text(text: str) -> str
├── analyze_technical_seo(title, content, keyword) -> Dict[str, Any]
└── Constants: STOPWORDS_ID, stemmer (singleton)

html_service.py
└── analyze_html_structure(html_content, keyword, base_url?) -> Dict[str, Any]

ninerouter_service.py
└── call_9router_for_geo(title, content, keyword) -> Dict[str, Any]

schema_service.py
├── generate_newsarticle_jsonld(data: SchemaJSONLDRequest) -> Dict[str, Any]
└── render_html_snippet(schema: Dict) -> str
```

---

## Alur Data per Endpoint

### POST /api/v1/seo/analyze

```
┌──────────────────────────────────────────────────────────────┐
│ INPUT: ArticleAnalysisRequest                                │
│   {title, content, focus_keyword, category?, use_ai_analysis?│
└─────────────────────────────┬────────────────────────────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
     ┌────────────┐  ┌────────────┐  ┌─────────────────┐
     │ technical  │  │    html    │  │   ninerouter    │
     │ _service   │  │  _service  │  │   _service      │
     │            │  │            │  │ (if use_ai=true)│
     └─────┬──────┘  └─────┬──────┘  └───────┬─────────┘
           │               │                  │
           ▼               ▼                  ▼
    tech_res{           html_res{          geo_res{
     seo_score,          headings,          eeat_score,
     keyword_density,    images,            experience,
     headline_score,     links,             expertise,
     suggestions[]       suggestions[]      authoritativeness,
    }                   }                   trustworthiness
                                           }
           │               │                  │
           └───────────────┼──────────────────┘
                           ▼
                  ┌─────────────────┐
                  │  AGGREGATION    │
                  │                 │
                  │ overall_score = │
                  │ tech*0.6 +      │
                  │ eeat*0.4        │
                  │                 │
                  │ suggestions =   │
                  │ dedup merge all │
                  └────────┬────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ OUTPUT: {status, data: {news_analysis, eeat_analysis,       │
│          html_structure_analysis, seo_suggestions,           │
│          overall_score, combined_suggestions}, provider}     │
└──────────────────────────────────────────────────────────────┘
```

### POST /api/v1/seo/analyze-url

```
┌──────────────────────────────────────┐
│ INPUT: URLAnalysisRequest            │
│   {url, focus_keyword, use_ai?}      │
└──────────────────┬───────────────────┘
                   ▼
          ┌─────────────────┐
          │  newspaper4k    │
          │  Article()      │
          │  .download()    │
          │  .parse()       │
          └────────┬────────┘
                   │
          Extract: title, text, html,
                   authors, publish_date,
                   top_image
                   │
          ┌────────┴────────────┐
          │ Truncate text       │
          │ ke 3000 chars       │
          │ (untuk AI prompt)   │
          └────────┬────────────┘
                   │
                   ▼
          Same pipeline as /analyze
          + url_metadata in response
```

### POST /api/v1/seo/schema-jsonld

```
┌─────────────────────────────────────────┐
│ INPUT: SchemaJSONLDRequest              │
│   {title, description, author_name, ...}│
└──────────────────┬──────────────────────┘
                   ▼
     ┌──────────────────────────┐
     │ generate_newsarticle     │
     │ _jsonld()                │
     │                          │
     │ - headline[:110]         │
     │ - Conditional: dateModified │
     │ - Conditional: image     │
     └────────────┬─────────────┘
                  │
                  ▼
     ┌──────────────────────────┐
     │ render_html_snippet()    │
     │ → <script type="ld+json">│
     └────────────┬─────────────┘
                  ▼
┌─────────────────────────────────────────┐
│ OUTPUT: {status, data: {jsonld,         │
│          html_snippet}}                 │
└─────────────────────────────────────────┘
```

---

## Service Details

### Technical Service (`technical_service.py`)

**Tanggung jawab:** Analisis SEO teknis berbasis aturan dan NLP lokal.

**Komponen utama:**
- **PySastrawi Stemmer** — Singleton instance, digunakan untuk stemming bahasa Indonesia
- **clean_text()** — Strip HTML tags, hapus karakter khusus, lowercase
- **Keyword density** — `(stemmed_keyword_count / total_words) × 100`
- **Keyword-in-title** — Pencocokan stopword-aware, order-independent
- **5W1H detection** — Kata-kata kunci: apa, siapa, dimana, kapan, mengapa, bagaimana + nama lokasi

**Scoring algorithm:**
```
Base score = 100
Penalties:
  - Judul < 40 atau > 70 chars:    -10
  - Keyword tidak di judul:         -15
  - Density < 0.8%:                 -10
  - Density > 3.0% (stuffing):      -20
  - Total kata < 250:               -15
Minimum score = 0
```

### HTML Service (`html_service.py`)

**Tanggung jawab:** Audit struktur HTML konten artikel.

**Analisis yang dilakukan:**
1. **Heading Audit** — Enumerasi H2/H3, cek keberadaan keyword di subheading (stopword-aware)
2. **Image Alt Audit** — Identifikasi gambar tanpa alt text, report sumber (max 10)
3. **Link Audit** — Pisahkan internal vs external link, extract domain external (sorted)

**Input khusus:** `base_url` parameter (opsional) digunakan untuk membedakan internal/external link.

### NineRouter Service (`ninerouter_service.py`)

**Tanggung jawab:** Evaluasi kualitatif GEO & E-E-A-T via external LLM.

**Alur:**
1. Compose prompt evaluasi dalam Bahasa Indonesia
2. POST ke 9Router API (format OpenAI-compatible)
3. Parse response JSON dari AI (strip markdown code fences)
4. **Graceful fallback**: Jika gagal (timeout, error, parsing failure), kembalikan objek dengan semua skor 0

**Konfigurasi:**
- URL dan API key dari `.env`
- Model: `ag/gemini-pro-agent`
- Temperature: `0.2` (konsisten)
- Timeout: `30 detik`

### Schema Service (`schema_service.py`)

**Tanggung jawab:** Generate NewsArticle Schema.org JSON-LD.

**Fitur:**
- Headline otomatis dipotong ke 110 karakter (rekomendasi Google)
- `dateModified` dan `image` kondisional (hanya jika diisi)
- `render_html_snippet()` menghasilkan `<script type="application/ld+json">` siap paste

---

## External Dependencies

| Library | Versi | Fungsi | Wajib |
|---|---|---|---|
| `fastapi` | latest | Web framework | ✅ |
| `uvicorn[standard]` | latest | ASGI server | ✅ |
| `gunicorn` | latest | Production WSGI/ASGI server | ❌ (production only) |
| `pydantic` | latest | Data validation | ✅ |
| `requests` | latest | HTTP client (untuk 9Router) | ✅ |
| `httpx` | latest | Async HTTP client (reserved) | ❌ |
| `PySastrawi` | latest | Indonesian stemmer | ✅ |
| `newspaper4k` | latest | Article scraping | ✅ (untuk endpoint /analyze-url) |
| `beautifulsoup4` | latest | HTML parsing | ✅ |
| `lxml` | latest | HTML/XML parser backend | ✅ |
| `python-dotenv` | latest | Environment variable loader | ✅ |

### External Services

| Service | Fungsi | Wajib |
|---|---|---|
| 9Router AI Proxy Gateway | LLM gateway untuk evaluasi GEO/E-E-A-T | ❌ (opsional) |

---

## Keputusan Desain

### Mengapa PySastrawi (bukan NLTK/spaCy)?

PySastrawi dirancang khusus untuk bahasa Indonesia dengan kamus kata dasar yang lengkap. NLTK dan spaCy memerlukan model bahasa Indonesia yang terpisah dan kurang akurat untuk stemming bahasa Indonesia.

### Mengapa 9Router (bukan direct LLM call)?

9Router berfungsi sebagai proxy gateway yang:
- Mengelola routing ke berbagai model LLM
- Menyediakan fallback otomatis antar model
- Menggunakan format API OpenAI-compatible, sehingga mudah diganti

### Mengapa Hybrid Scoring (60/40)?

- **60% teknis**: Faktor-faktor SEO teknis bersifat deterministik dan bisa diandalkan
- **40% AI**: Evaluasi E-E-A-T bersifat kualitatif dan tergantung ketersediaan LLM
- Jika AI tidak tersedia, score tetap bermakna (100% teknis)

### Mengapa newspaper4k (bukan Scrapy/Selenium)?

newspaper4k dirancang untuk ekstrasi artikel berita — langsung extract title, authors, publish date, dan text tanpa konfigurasi kompleks. Limitation: tidak bisa handle JS-rendered pages.

### Mengapa Sugestions Deduplicated?

Saran dari berbagai service (teknis, HTML, E-E-A-T) bisa overlap. `dict.fromkeys()` digunakan karena menjaga urutan pertama kemunculan (tidak seperti `set()`).

---

## Skalabilitas & Limitasi

### Limitasi Saat Ini

- **Single process**: Uvicorn default menjalankan 1 worker
- **Synchronous HTTP**: `requests` library blocking. 9Router call bisa memperlambat response
- **No caching**: Setiap request dihitung ulang dari awal
- **No auth**: Endpoint terbuka tanpa autentikasi
- **No rate limiting**: Tidak ada pembatasan request

### Rekomendasi Scaling

| Aspek | Rekomendasi |
|---|---|
| **Multi-worker** | Gunakan `gunicorn -w 4 -k uvicorn.workers.UvicornWorker` |
| **Async HTTP** | Migrasi `requests` → `httpx` (async) untuk non-blocking 9Router call |
| **Caching** | Tambahkan Redis/in-memory cache untuk hasil analisis URL yang sama |
| **Auth** | Implementasi API key middleware atau OAuth2 |
| **Rate limiting** | Tambahkan `slowapi` atau nginx rate limiting |
| **Monitoring** | Integrasi Prometheus metrics + structured logging |
