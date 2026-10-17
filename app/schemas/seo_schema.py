from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ArticleAnalysisRequest(BaseModel):
    title: str = Field(..., examples=["Polri Tindak Lanjut Judi Online di Kaltim"])
    content: str = Field(..., examples=["Balikpapan - Kepolisian Daerah Kalimantan Timur melakukan tindakan tegas..."])
    focus_keyword: Optional[str] = Field(None, description="Kata kunci fokus SEO (opsional, akan di-generate otomatis oleh AI jika kosong)", examples=["Judi Online Kaltim"])
    category: Optional[str] = Field(None, examples=["Hukum"])
    seo_title: Optional[str] = Field(None, description="Judul SEO aktif saat ini (opsional untuk audit)", examples=["Polri Tindak Judi Online di Kaltim"])
    meta_description: Optional[str] = Field(None, description="Deskripsi meta aktif saat ini (opsional untuk audit)", examples=["Kepolisian Daerah Kalimantan Timur menindak tegas pelaku judi online..."])
    use_ai_analysis: Optional[bool] = Field(True, description="Sertakan analisis GEO & E-E-A-T via 9Router")
    base_url: Optional[str] = Field(None, description="URL situs utama untuk deteksi link internal (opsional)", examples=["https://borneoflash.com"])


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., examples=["https://kaltimtoday.co/berita-judi-online"])
    focus_keyword: Optional[str] = Field(None, description="Kata kunci fokus (opsional, akan diekstrak otomatis jika kosong)", examples=["Judi Online Kaltim"])
    use_ai_analysis: Optional[bool] = Field(True, description="Sertakan analisis GEO & E-E-A-T via 9Router")
    is_own_site: Optional[bool] = Field(None, description="Set True jika URL adalah web sendiri (BorneoFlash), False jika kompetitor. Default None (auto-detect domain)", examples=[False])


class SchemaJSONLDRequest(BaseModel):
    title: str = Field(..., examples=["Polri Tindak Lanjut Judi Online di Kaltim"])
    description: str = Field(..., examples=["Kepolisian Daerah Kaltim melakukan tindakan tegas terhadap pelaku judi online."])
    author_name: str = Field(..., examples=["Redaksi BorneoFlash"])
    publisher_name: str = Field(..., examples=["BorneoFlash Media"])
    publisher_logo_url: str = Field(..., examples=["https://borneoflash.com/logo.png"])
    date_published: str = Field(..., examples=["2026-09-24T03:00:00+08:00"])
    date_modified: Optional[str] = Field(None, examples=["2026-09-24T04:00:00+08:00"])
    image_url: Optional[str] = Field(None, examples=["https://borneoflash.com/img/berita.jpg"])
    article_url: str = Field(..., examples=["https://borneoflash.com/polri-judi-online-kaltim"])


class TaxonomyAnalysisRequest(BaseModel):
    name: str = Field(..., examples=["Balikpapan"])
    description: Optional[str] = Field(None, description="Deskripsi taksonomi saat ini", examples=["Kumpulan berita dan informasi dari Kota Balikpapan"])
    taxonomy_type: Optional[str] = Field("category", description="Tipe taksonomi: category, post_tag, newstopic", examples=["category"])
    use_ai_analysis: Optional[bool] = Field(True, description="Sertakan analisis AI via 9Router")


class URLRewriteRequest(BaseModel):
    url: str = Field(..., examples=["https://kaltim.tribunnews.com/tribun-etam/1168317/rudianto-salip-abdunnur-di-putaran-akhir-74-suara-antarkan-guru-besar-kehutanan-jadi-rektor-unmul"])
    focus_keyword: Optional[str] = Field(None, description="Kata kunci fokus (opsional, jika kosong ditentukan otomatis oleh AI)", examples=["Rektor Unmul 2026"])
    tone: Optional[str] = Field(None, description="Gaya penulisan: straight_news, investigative, feature, press_release (opsional, jika kosong dipilih otomatis oleh AI)", examples=["straight_news"])
    local_perspective: Optional[str] = Field(None, description="Fokus perspektif lokal redaksi (opsional, jika kosong dianalisis otomatis oleh AI)", examples=["Kalimantan Timur"])


class ContentImprovementRequest(BaseModel):
    title: str = Field(..., examples=["Tatap PEDA KTNA 2028, Wabup Paser Terima Audiensi Pengurus Provinsi dan Kabupaten"])
    content: str = Field(..., examples=["Pemerintah Kabupaten Paser secara resmi menyatakan kesiapannya untuk melakoni peran sebagai tuan rumah..."])
    focus_keyword: Optional[str] = Field(None, description="Kata kunci fokus target (opsional, jika kosong diekstrak otomatis)", examples=["PEDA KTNA 2028"])
    mode: Optional[str] = Field("all", description="Mode perbaikan: all, readability, lede, subheadings, headlines", examples=["all"])
    expand_content: Optional[bool] = Field(False, description="Kembangkan naskah jika kata < 350 kata", examples=[False])


# ==============================================================================
# V3.0 SCHEMAS: Google Trends, Instant Indexing, Search Console & Audit
# ==============================================================================

class TrendingTopicItem(BaseModel):
    title: str
    approx_traffic: Optional[str] = None
    pub_date: Optional[str] = None
    description: Optional[str] = None
    news_title: Optional[str] = None
    news_snippet: Optional[str] = None
    news_url: Optional[str] = None
    news_source: Optional[str] = None
    picture_url: Optional[str] = None


class TrendingTopicsResponse(BaseModel):
    status: str = "success"
    geo: str = "ID"
    total: int
    items: List[TrendingTopicItem]


class AutocompleteRequest(BaseModel):
    query: str = Field(..., description="Kueri awal pencarian Google", examples=["insentif guru paud"])
    geo: Optional[str] = Field("ID", description="Wilayah pencarian (default: ID)", examples=["ID"])
    lang: Optional[str] = Field("id", description="Bahasa pencarian (default: id)", examples=["id"])


class PeopleAlsoAskRequest(BaseModel):
    keyword: str = Field(..., description="Kata kunci utama artikel berita", examples=["insentif guru paud samarinda"])
    geo: Optional[str] = Field("ID", examples=["ID"])


class CompareTrendsRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=2, max_length=5, description="Daftar 2-5 kata kunci untuk dibandingkan minat pencariannya", examples=[["insentif guru paud", "gaji guru paud"]])
    geo: Optional[str] = Field("ID", examples=["ID"])


class IndexingNotificationRequest(BaseModel):
    url: str = Field(..., description="URL lengkap berita yang ingin diindeks seketika oleh Google", examples=["https://borneoflash.com/insentif-guru-paud-samarinda"])
    action: Optional[str] = Field("URL_UPDATED", description="Tipe notifikasi: URL_UPDATED atau URL_DELETED", examples=["URL_UPDATED"])


class IndexingBatchRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1, max_length=100, description="Daftar URL berita untuk diindeks serentak")
    action: Optional[str] = Field("URL_UPDATED", description="Tipe notifikasi: URL_UPDATED atau URL_DELETED", examples=["URL_UPDATED"])


class GSCPerformanceRequest(BaseModel):
    url: str = Field(..., description="URL lengkap artikel BorneoFlash untuk memeriksa metrik Google riil", examples=["https://borneoflash.com/insentif-guru-paud-samarinda"])
    days: Optional[int] = Field(28, description="Rentang hari histori (misal: 7, 28, 90 hari)", examples=[28])


class GSCOpportunitiesRequest(BaseModel):
    site_url: Optional[str] = Field(None, description="URL situs Search Console (opsional, jika kosong dibaca dari .env)", examples=["sc-domain:borneoflash.com"])
    days: Optional[int] = Field(28, description="Rentang histori hari", examples=[28])
    min_impressions: Optional[int] = Field(100, description="Batas minimal tayang di Google", examples=[100])
    max_ctr: Optional[float] = Field(0.05, description="Batas maksimal CTR (misal 0.05 = 5%)", examples=[0.05])


class CannibalizationArticleItem(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., examples=["Insentif Guru PAUD Samarinda Diperjuangkan"])
    focus_keyword: Optional[str] = Field(None, examples=["insentif guru paud samarinda"])
    url: Optional[str] = Field(None, examples=["https://borneoflash.com/artikel-1"])


class CannibalizationAuditRequest(BaseModel):
    articles: List[CannibalizationArticleItem] = Field(..., min_length=2, description="Daftar artikel yang ingin diaudit potensi saling bentur kata kuncinya")

