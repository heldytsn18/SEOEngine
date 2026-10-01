import pytest
from app.services.technical_service import (
    clean_text,
    split_sentences_id,
    split_paragraphs,
    extract_focus_keyword_heuristic,
    analyze_lede_5w1h,
    analyze_readability,
    analyze_technical_seo
)


def test_clean_text():
    html = "<p>Halo <b>Balikpapan</b>, ini adalah uji coba SEO!</p>"
    cleaned = clean_text(html)
    assert cleaned == "halo balikpapan ini adalah uji coba seo"


def test_split_sentences_id_abbreviations():
    text = (
        "BALIKPAPAN - Dr. H. Rahmad Mas'ud, S.E., M.E. menghadiri rapat koordinasi "
        "pukul 14.30 WITA di Kantor Pemkot Balikpapan. "
        "Pertumbuhan ekonomi Kaltim mencapai 5.5% pada kuartal ketiga tahun ini. "
        "Kegiatan berjalan lancar hingga sore hari."
    )
    sentences = split_sentences_id(text)
    assert len(sentences) == 3
    assert "Dr. H. Rahmad Mas'ud, S.E., M.E." in sentences[0]
    assert "14.30 WITA" in sentences[0]
    assert "5.5%" in sentences[1]


def test_extract_focus_keyword_heuristic():
    title = "Polda Kaltim Tindak Tegas Pelaku Judi Online di Balikpapan"
    kw = extract_focus_keyword_heuristic(title)
    assert len(kw.split()) <= 4
    assert "polda kaltim" in kw.lower() or "judi online" in kw.lower() or "tindak tegas" in kw.lower()


def test_analyze_lede_5w1h_complete():
    lede = (
        "BALIKPAPAN - Kementerian Ketenagakerjaan (Kemnaker) mendorong generasi muda di Balikpapan "
        "untuk menguasai teknologi kecerdasan buatan (AI) guna meningkatkan produktivitas kerja "
        "di era digital, Rabu (1/10/2026)."
    )
    res = analyze_lede_5w1h(lede)
    assert res["when"] is True
    assert res["where"] is True
    assert res["who"] is True
    assert res["what"] is True
    assert res["is_complete"] is True
    assert res["elements_count"] >= 4


def test_analyze_readability():
    sentences = [
        "Kementerian Ketenagakerjaan mendorong generasi muda di Balikpapan untuk menguasai teknologi AI.",
        "Pelatihan digital ini bertujuan meningkatkan produktivitas kerja para pencari kerja lokal.",
        "Program tersebut disambut antusias oleh ratusan peserta pemuda dan mahasiswa setempat."
    ]
    paragraphs = [
        "Kementerian Ketenagakerjaan mendorong generasi muda di Balikpapan untuk menguasai teknologi AI. Pelatihan digital ini bertujuan meningkatkan produktivitas kerja para pencari kerja lokal.",
        "Program tersebut disambut antusias oleh ratusan peserta pemuda dan mahasiswa setempat."
    ]
    words_count = sum(len(s.split()) for s in sentences)
    score, details, suggestions = analyze_readability(sentences, paragraphs, words_count)
    assert 0 <= score <= 100
    assert details["asl"] > 0
    assert details["total_sentences"] == 3
    assert details["total_paragraphs"] == 2


def test_analyze_technical_seo_long_tail_contiguous():
    title = "Kemnaker Dorong Generasi Muda Balikpapan Kuasai AI untuk Tingkatkan Produktivitas Kerja"
    content = (
        "BALIKPAPAN - Kementerian Ketenagakerjaan mendorong generasi muda di Balikpapan untuk menguasai "
        "teknologi kecerdasan buatan guna meningkatkan produktivitas kerja di era transformasi digital, Rabu (1/10/2026).\n\n"
        "Kepala Dinas Ketenagakerjaan Kota Balikpapan menyatakan bahwa pemahaman AI generasi muda produktivitas "
        "menjadi kunci utama daya saing daerah di masa depan.\n\n"
        "Peserta menyambut baik program ini agar mampu bersaing di pasar kerja global."
    )
    keyword = "AI generasi muda produktivitas"
    res = analyze_technical_seo(title, content, keyword)

    assert res["keyword_count"] >= 1
    assert res["keyword_coverage"] == 100.0
    assert res["keyword_density_status"] == "Ideal"
    assert res["lede_quality"] == "Good"
    assert res["lede_has_5w1h"] is True
    assert res["seo_score"] > 60


def test_analyze_technical_seo_long_tail_spread_coverage():
    title = "Kemnaker Dorong Generasi Muda Balikpapan Kuasai AI untuk Tingkatkan Produktivitas Kerja"
    content = (
        "BALIKPAPAN - Kementerian Ketenagakerjaan mendorong generasi muda di Balikpapan untuk menguasai "
        "teknologi kecerdasan buatan (AI) guna meningkatkan produktivitas kerja di era transformasi digital, Rabu (1/10/2026).\n\n"
        "Inovasi teknologi digital menjadi kunci utama peningkatan kualitas sumber daya manusia lokal.\n\n"
        "Peserta menyambut baik program pelatihan ini agar mampu bersaing di pasar kerja modern."
    )
    keyword = "AI generasi muda produktivitas"
    res = analyze_technical_seo(title, content, keyword)

    # Kata tersebar lengkap (AI, generasi, muda, produktivitas) tapi belum frasa utuh berurutan
    assert res["keyword_count"] == 0
    assert res["keyword_coverage"] == 100.0
    assert "Sebaran kata lengkap" in res["keyword_density_status"]
    # Saran memberikan panduan jelas untuk menuliskan frasa lengkap
    has_spread_suggestion = any("sebaran 100%" in s for s in res["technical_suggestions"])
    assert has_spread_suggestion is True


def test_analyze_technical_seo_keyword_absent():
    title = "Pembangunan Jembatan Baru di Penajam Paser Utara Berjalan Lancar"
    content = (
        "PENAJAM - Pemerintah Kabupaten Penajam Paser Utara terus mempercepat pembangunan infrastruktur jalan "
        "dan jembatan untuk mendukung konektivitas antarwilayah, Senin (28/9/2026).\n\n"
        "Proyek ini ditargetkan rampung pada akhir tahun guna mempermudah mobilitas masyarakat dan distribusi logistik."
    )
    keyword = "kuliner kepiting balikpapan"
    res = analyze_technical_seo(title, content, keyword)

    assert res["keyword_count"] == 0
    assert res["keyword_coverage"] == 0.0
    assert res["keyword_density_status"] == "Terlalu rendah"
    has_absent_msg = any("belum tertulis di dalam naskah" in s for s in res["technical_suggestions"])
    assert has_absent_msg is True
