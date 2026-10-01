# BorneoFlash SEO Engine — API Reference

> **Base URL:** `http://localhost:8000`
> **Swagger UI:** `http://localhost:8000/docs`
> **ReDoc:** `http://localhost:8000/redoc`
> **Version:** 2.0.0

---

## Daftar Isi

1. [GET /](#get-)
2. [GET /health](#get-health)
3. [POST /api/v1/seo/analyze](#post-apiv1seoanalyze)
4. [POST /api/v1/seo/analyze-url](#post-apiv1seoanalyze-url)
5. [POST /api/v1/seo/schema-jsonld](#post-apiv1seoschema-jsonld)
6. [POST /api/v1/seo/analyze-taxonomy](#post-apiv1seoanalyze-taxonomy)
7. [Error Responses](#error-responses)
8. [Tipe Data Response](#tipe-data-response)

---

## GET /

Status server.

**Response:**
```json
{
  "status": "online",
  "service": "BorneoFlash SEO Engine Microservice",
  "version": "2.0.0"
}
```

---

## GET /health

Health check komponen.

**Response:**
```json
{
  "status": "ok",
  "components": {
    "pysastrawi": "ready",
    "fastapi": "ready",
    "newspaper4k": "ready"
  }
}
```

---

## POST /api/v1/seo/analyze

Analisis draf artikel berita: skor teknis SEO, struktur HTML, dan evaluasi GEO/E-E-A-T.

### Request Body

| Field | Type | Required | Default | Deskripsi |
|---|---|---|---|---|
| `title` | string | ✅ | — | Judul artikel |
| `content` | string | ✅ | — | Konten artikel (bisa berisi HTML) |
| `focus_keyword` | string | ✅ | — | Kata kunci fokus SEO |
| `category` | string | ❌ | `null` | Kategori berita |
| `use_ai_analysis` | boolean | ❌ | `true` | Aktifkan analisis GEO via 9Router |
| `base_url` | string | ❌ | `null` | URL utama untuk deteksi *internal link* |

**Contoh Request:**
```json
{
  "title": "Polri Tindak Lanjut Judi Online di Kaltim",
  "content": "<h2>Penangkapan di Balikpapan</h2><p>Kepolisian Daerah Kalimantan Timur melakukan tindakan tegas terhadap pelaku judi online...</p><img src='bukti.jpg' alt='Barang bukti judi online'>",
  "focus_keyword": "Judi Online Kaltim",
  "category": "Hukum",
  "use_ai_analysis": true,
  "base_url": "https://borneoflash.com"
}
```

### Response

```json
{
  "status": "success",
  "data": {
    "overall_score": 72,
    "news_analysis": {
      "seo_score": 75,
      "readability_score": 100,
      "headline_score": 100,
      "headline_issues": [],
      "headline_suggestion": "",
      "lede_quality": "Bagus",
      "lede_word_count": 50,
      "lede_has_5w1h": true,
      "lede_has_keyword": true,
      "keyword_density": 1.43,
      "keyword_density_status": "Ideal",
      "technical_suggestions": ["..."]
    },
    "eeat_analysis": {
      "eeat_score": 68,
      "experience": {
        "score": 60,
        "has_firsthand_experience": false,
        "suggestions": ["Tambahkan kutipan langsung dari narasumber."]
      },
      "expertise": {
        "score": 70,
        "has_expert_sources": true,
        "has_data_statistics": false,
        "suggestions": ["Sertakan data statistik pendukung."]
      },
      "authoritativeness": {
        "score": 75,
        "has_official_sources": true,
        "has_citations": true,
        "suggestions": []
      },
      "trustworthiness": {
        "score": 65,
        "is_balanced": false,
        "has_verification": false,
        "suggestions": ["Tambahkan perspektif dari pihak lain."]
      }
    },
    "html_structure_analysis": {
      "headings": {
        "h2_count": 2,
        "h3_count": 1,
        "h2_texts": ["Penangkapan di Balikpapan", "..."],
        "h3_texts": ["..."],
        "keyword_in_subheading": true
      },
      "images": {
        "total": 3,
        "with_alt": 2,
        "without_alt": 1,
        "missing_alt_sources": ["gambar.jpg"]
      },
      "links": {
        "internal_count": 5,
        "external_count": 2,
        "external_domains": ["bps.go.id", "polri.go.id"]
      },
      "html_suggestions": ["..."]
    },
    "seo_suggestions": {
      "focus_keyword": "Judi Online Kaltim",
      "seo_title": "Polri Tindak Lanjut Judi Online di Kaltim",
      "meta_description": "Kepolisian Daerah Kalimantan Timur melakukan..."
    },
    "editor_notes": "Perbaiki tanggal kejadian yang tercantum karena ini adalah kesalahan fatal untuk berita. Perpendek judul agar lebih ringkas dan fokus pada inti berita. Tambahkan kutipan langsung dari pihak kepolisian.",
    "combined_suggestions": [
      "Saran teknis 1",
      "Saran HTML 1",
      "Saran E-E-A-T 1"
    ]
  },
  "provider": "fastapi"
}
```

### Detail Skor

| Komponen | Bobot | Sumber |
|---|---|---|
| `news_analysis.seo_score` | 60% | PySastrawi + rule-based |
| `eeat_analysis.eeat_score` | 40% | 9Router AI |
| `overall_score` | — | `(seo_score × 0.6) + (eeat_score × 0.4)` |

> **Catatan:** Jika `use_ai_analysis: false`, maka `overall_score = seo_score` dan `eeat_analysis` mengembalikan semua skor 0.

### Penalti Skor Teknis

| Kondisi | Penalti |
|---|---|
| Judul < 40 atau > 70 karakter | -10 |
| Keyword tidak ada di judul | -15 |
| Keyword density < 0.8% | -10 |
| Keyword density > 3.0% (stuffing) | -20 |
| Total kata < 250 | -15 |

### news_analysis Fields

| Field | Type | Deskripsi |
|---|---|---|
| `seo_score` | integer | Skor teknis SEO (0–100) |
| `readability_score` | integer | Skor keterbacaan (0–100) |
| `headline_score` | integer | Skor judul (40/70/100) |
| `headline_issues` | array | Masalah spesifik pada judul |
| `headline_suggestion` | string | Saran perbaikan judul (kosong jika sudah baik) |
| `lede_quality` | string | `"Bagus"` atau `"Perlu Perbaikan"` |
| `lede_word_count` | integer | Jumlah kata di lead (max 50) |
| `lede_has_5w1h` | boolean | Apakah mengandung elemen 5W1H |
| `lede_has_keyword` | boolean | Apakah keyword ada di 50 kata pertama (lead paragraf) |
| `keyword_density` | float | Persentase kerapatan kata kunci |
| `keyword_density_status` | string | `"Ideal"`, `"Terlalu rendah"`, atau `"Terlalu tinggi"` |
| `technical_suggestions` | array | Daftar saran perbaikan teknis |

---

## POST /api/v1/seo/analyze-url

Scrape dan analisis URL artikel kompetitor menggunakan newspaper4k.

### Request Body

| Field | Type | Required | Default | Deskripsi |
|---|---|---|---|---|
| `url` | string | ✅ | — | URL artikel yang akan dianalisis |
| `focus_keyword` | string | ✅ | — | Kata kunci fokus untuk perbandingan |
| `use_ai_analysis` | boolean | ❌ | `true` | Aktifkan analisis GEO via 9Router |

**Contoh Request:**
```json
{
  "url": "https://kaltimtoday.co/berita-judi-online-kaltim",
  "focus_keyword": "Judi Online Kaltim",
  "use_ai_analysis": true
}
```

### Response

Struktur sama dengan `/analyze`, ditambah field `url_metadata`:

```json
{
  "status": "success",
  "data": {
    "overall_score": 65,
    "news_analysis": { "..." },
    "eeat_analysis": { "..." },
    "html_structure_analysis": { "..." },
    "seo_suggestions": {
      "focus_keyword": "Judi Online Kaltim",
      "seo_title": "Judul Artikel dari Website",
      "meta_description": "150 karakter pertama dari konten..."
    },
    "editor_notes": "Sertakan tautan ke sumber resmi (misalnya, situs instansi) jika ada rilis pers terkait untuk meningkatkan Authoritativeness. Perjelas sumber informasi artikel.",
    "keyword_analysis": {
      "user_provided_keyword": "",
      "detected_competitor_keyword": "Pemilihan Rektor Unmul",
      "recommended_focus_keyword": "Rudianto Salip Abdunnur",
      "meta_keywords_from_page": [
        "Pemilihan Rektor Unmul",
        "Unmul",
        "Universitas Mulawarman",
        "Rudianto Amirta"
      ],
      "keyword_variations": [
        "Unmul",
        "Universitas Mulawarman",
        "Rudianto Amirta"
      ],
      "notes": "Kata kunci terdeteksi yang dibidik kompetitor: 'Pemilihan Rektor Unmul'. Rekomendasi kata kunci fokus terbaik untuk SEO artikel Anda: 'Rudianto Salip Abdunnur'."
    },
    "url_metadata": {
      "url": "https://kaltimtoday.co/berita-judi-online-kaltim",
      "domain": "kaltimtoday.co",
      "title": "Judul Artikel dari Website",
      "authors": ["Nama Penulis"],
      "publish_date": "2026-09-20 10:00:00",
      "top_image": "https://kaltimtoday.co/img/header.jpg",
      "meta_description": "Ringkasan meta deskripsi asli kompetitor...",
      "canonical_url": "https://kaltimtoday.co/berita-judi-online-kaltim",
      "word_count": 420,
      "reading_time_minutes": 2
    },
    "competitor_opportunities": [
      "Kata kunci terdeteksi yang dibidik kompetitor: 'Pemilihan Rektor Unmul'. Untuk menyalip di hasil pencarian atau mengoptimasi artikel sendiri, gunakan rekomendasi kata kunci fokus: 'Rudianto Salip Abdunnur' (variasi: Unmul, Universitas Mulawarman, Rudianto Amirta).",
      "Panjang artikel kompetitor standar (420 kata). Tambahkan sudut pandang eksklusif atau latar belakang peristiwa untuk menyalipnya.",
      "Kompetitor tidak mencantumkan tautan ke sumber resmi/pemerintah. Cantumkan rujukan resmi untuk skor E-E-A-T yang lebih kuat di Google News."
    ],
    "combined_suggestions": ["..."]
  },
  "provider": "fastapi"
}
```

### Catatan Penting

- **Deteksi Kata Kunci Otomatis (Jika `focus_keyword` Kosong)**: Jika pengguna tidak mengisi `focus_keyword` (`""`), engine mengekstrak kata kunci target kompetitor dari tag `<meta name="keywords">`, `<meta name="news_keywords">`, dan analisis AI. Engine kemudian memberikan **rekomendasi kata kunci fokus terbaik untuk SEO** beserta variasi long-tail pada field `keyword_analysis` dan `seo_suggestions.focus_keyword`.
- **Anti-Bot & WAF Bypass**: Dilengkapi header browser modern rotasi (Chrome, Firefox, Safari) untuk mencegah blokir `403 Forbidden` dari portal berita besar (Tribunnews, Kompas, Detik).
- **Dual Engine Extraction**: Menggabungkan `newspaper4k` dan fallback `BeautifulSoup` (mengekstrak selektor kontainer artikel Indonesia jika heuristik newspaper kosong).
- Konten yang dikirim ke AI dibatasi **3000 karakter** untuk efisiensi prompt.
- Jika URL tidak bisa diakses atau domain tidak merespons, API mengembalikan **HTTP 400**.

---

## POST /api/v1/seo/schema-jsonld

Generate struktur `NewsArticle` Schema.org JSON-LD yang valid untuk Google News.

### Request Body

| Field | Type | Required | Default | Deskripsi |
|---|---|---|---|---|
| `title` | string | ✅ | — | Judul artikel (dipotong max 110 karakter oleh engine) |
| `description` | string | ✅ | — | Deskripsi meta artikel |
| `author_name` | string | ✅ | — | Nama penulis |
| `publisher_name` | string | ✅ | — | Nama organisasi penerbit |
| `publisher_logo_url` | string | ✅ | — | URL logo penerbit |
| `date_published` | string | ✅ | — | Tanggal terbit (format ISO 8601) |
| `date_modified` | string | ❌ | `null` | Tanggal modifikasi (format ISO 8601) |
| `image_url` | string | ❌ | `null` | URL gambar utama artikel |
| `article_url` | string | ✅ | — | URL halaman artikel |

**Contoh Request:**
```json
{
  "title": "Polri Tindak Lanjut Judi Online di Kaltim",
  "description": "Kepolisian Daerah Kaltim melakukan tindakan tegas terhadap pelaku judi online.",
  "author_name": "Redaksi BorneoFlash",
  "publisher_name": "BorneoFlash Media",
  "publisher_logo_url": "https://borneoflash.com/logo.png",
  "date_published": "2026-09-24T03:00:00+08:00",
  "date_modified": "2026-09-24T04:00:00+08:00",
  "image_url": "https://borneoflash.com/img/berita.jpg",
  "article_url": "https://borneoflash.com/polri-judi-online-kaltim"
}
```

### Response

```json
{
  "status": "success",
  "data": {
    "jsonld": {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": "Polri Tindak Lanjut Judi Online di Kaltim",
      "description": "Kepolisian Daerah Kaltim melakukan tindakan tegas terhadap pelaku judi online.",
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": "https://borneoflash.com/polri-judi-online-kaltim"
      },
      "author": {
        "@type": "Person",
        "name": "Redaksi BorneoFlash"
      },
      "publisher": {
        "@type": "Organization",
        "name": "BorneoFlash Media",
        "logo": {
          "@type": "ImageObject",
          "url": "https://borneoflash.com/logo.png"
        }
      },
      "datePublished": "2026-09-24T03:00:00+08:00",
      "dateModified": "2026-09-24T04:00:00+08:00",
      "image": {
        "@type": "ImageObject",
        "url": "https://borneoflash.com/img/berita.jpg"
      },
      "url": "https://borneoflash.com/polri-judi-online-kaltim"
    },
    "html_snippet": "<script type=\"application/ld+json\">\n{...}\n</script>"
  }
}
```

### Cara Pakai

Salin nilai `html_snippet` dan paste ke dalam tag `<head>` halaman artikel untuk structured data Google News.

### Validasi

- Field `headline` otomatis dipotong ke **110 karakter** (rekomendasi Google)
- `dateModified` dan `image` hanya disertakan jika diisi di request
- Untuk validasi output, gunakan [Google Rich Results Test](https://search.google.com/test/rich-results)

---

## POST /api/v1/seo/analyze-taxonomy

Analisis SEO halaman arsip taksonomi berita (kategori, tag, topik khusus) via 9Router AI & Heuristik Lokal.

### Request Body

| Field | Tipe | Wajib | Deskripsi | Contoh |
|---|---|---|---|---|
| `name` | string | Ya | Nama taksonomi (kategori, tag, topik) | `"Balikpapan Pos"` |
| `description` | string | Tidak | Deskripsi taksonomi saat ini | `"Kumpulan berita seputar Balikpapan"` |
| `taxonomy_type` | string | Tidak | Tipe taksonomi: `category`, `post_tag`, `newstopic` (default: `"category"`) | `"category"` |
| `use_ai_analysis` | boolean | Tidak | Evaluasi AI via 9Router (default: `true`) | `true` |

```json
{
  "name": "Balikpapan Pos",
  "description": "Kumpulan berita seputar Kota Balikpapan dan Kalimantan Timur.",
  "taxonomy_type": "category",
  "use_ai_analysis": true
}
```

### Response

```json
{
  "status": "success",
  "data": {
    "seo_title": "Berita Balikpapan Pos Terkini Hari Ini | BorneoFlash",
    "meta_description": "Kumpulan berita Balikpapan Pos terbaru dan terlengkap. Simak liputan mendalam, fakta terkini, dan analisis peristiwa Balikpapan Pos di BorneoFlash.",
    "focus_keyword": "berita balikpapan pos",
    "seo_score": 85,
    "readability_score": 90,
    "suggestions": [
      "Sisipkan kata kunci target 'berita balikpapan pos' di kalimat pembuka deskripsi agar terdeteksi mesin pencari."
    ],
    "improved_description": "Halaman arsip kumpulan berita balikpapan pos, kabar terkini, dan liputan peristiwa seputar Balikpapan Pos. Menyajikan fakta terverifikasi dan ulasan terpercaya untuk pembaca di Kalimantan Timur dan sekitarnya."
  },
  "provider": "ninerouter"
}
```

---

## Error Responses

### HTTP Status Codes

| HTTP Code | Kondisi |
|---|---|
| 200 | Request berhasil |
| 400 | Konten kosong, URL tidak bisa diakses, atau parsing gagal |
| 422 | Request body tidak sesuai schema (field required hilang atau tipe salah) |
| 500 | Library belum terinstal atau internal error |

### Format Error

**HTTP 400/500 (HTTPException):**
```json
{
  "detail": "Pesan error deskriptif dalam Bahasa Indonesia"
}
```

**HTTP 422 (Validation Error):**
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Tipe Data Response

### E-E-A-T Analysis Object

Struktur objek `eeat_analysis` ketika `use_ai_analysis: true`:

```json
{
  "eeat_score": 68,
  "experience": {
    "score": 60,
    "has_firsthand_experience": false,
    "suggestions": ["string"]
  },
  "expertise": {
    "score": 70,
    "has_expert_sources": true,
    "has_data_statistics": false,
    "suggestions": ["string"]
  },
  "authoritativeness": {
    "score": 75,
    "has_official_sources": true,
    "has_citations": true,
    "suggestions": ["string"]
  },
  "trustworthiness": {
    "score": 65,
    "is_balanced": false,
    "has_verification": false,
    "suggestions": ["string"]
  }
}
```

Ketika `use_ai_analysis: false` atau 9Router gagal, semua skor bernilai `0` dan `suggestions` berisi array kosong (atau pesan error koneksi).

### HTML Structure Analysis Object

```json
{
  "headings": {
    "h2_count": 2,
    "h3_count": 1,
    "h2_texts": ["string"],
    "h3_texts": ["string"],
    "keyword_in_subheading": true
  },
  "images": {
    "total": 3,
    "with_alt": 2,
    "without_alt": 1,
    "missing_alt_sources": ["string (max 10 items)"]
  },
  "links": {
    "internal_count": 5,
    "external_count": 2,
    "external_domains": ["string (sorted)"]
  },
  "html_suggestions": ["string"]
}
```

### URL Metadata Object (khusus analyze-url)

```json
{
  "url": "string",
  "title": "string",
  "authors": ["string"],
  "publish_date": "string | null",
  "top_image": "string"
}
```
