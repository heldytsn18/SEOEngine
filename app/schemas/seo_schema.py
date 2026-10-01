from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ArticleAnalysisRequest(BaseModel):
    title: str = Field(..., examples=["Polri Tindak Lanjut Judi Online di Kaltim"])
    content: str = Field(..., examples=["Balikpapan - Kepolisian Daerah Kalimantan Timur melakukan tindakan tegas..."])
    focus_keyword: Optional[str] = Field(None, description="Kata kunci fokus SEO (opsional, akan di-generate otomatis oleh AI jika kosong)", examples=["Judi Online Kaltim"])
    category: Optional[str] = Field(None, examples=["Hukum"])
    use_ai_analysis: Optional[bool] = Field(True, description="Sertakan analisis GEO & E-E-A-T via 9Router")
    base_url: Optional[str] = Field(None, description="URL situs utama untuk deteksi link internal (opsional)", examples=["https://borneoflash.com"])


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., examples=["https://kaltimtoday.co/berita-judi-online"])
    focus_keyword: Optional[str] = Field(None, description="Kata kunci fokus (opsional, akan diekstrak otomatis jika kosong)", examples=["Judi Online Kaltim"])
    use_ai_analysis: Optional[bool] = Field(True, description="Sertakan analisis GEO & E-E-A-T via 9Router")


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
