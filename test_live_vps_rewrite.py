import requests
import json
import time

VPS_URL = "https://seo.borneoflash.com/api/v1/seo/rewrite-url"

test_urls = [
    "https://kaltimtoday.co/disdikbud-balikpapan-gelar-festival-tunas-bahasa-ibu-2024",
    "https://kaltim.tribunnews.com/tribun-etam/1168317/rudianto-salip-abdunnur-di-putaran-akhir-74-suara-antarkan-guru-besar-kehutanan-jadi-rektor-unmul",
    "https://borneoflash.com/polri-judi-online-kaltim"
]

for url in test_urls:
    print("\n" + "=" * 70)
    print(f"MENGUJI URL: {url}")
    print("Mode Otomatis: focus_keyword, tone, dan local_perspective KOSONG (None)")
    print("=" * 70)

    payload = {"url": url}
    start = time.time()
    try:
        res = requests.post(VPS_URL, json=payload, timeout=90)
        elapsed = time.time() - start
        print(f"Status: {res.status_code} ({elapsed:.2f}s)")
        if res.status_code == 200:
            data = res.json().get("data", {})
            art = data.get("article", {})
            seo = data.get("seo_metadata", {})
            qual = data.get("quality_metrics", {})
            src = data.get("source_metadata", {})

            print(f"\n[HASIL SUKSES]")
            print(f"Judul Baru      : {art.get('title')}")
            print(f"Featured Image  : {art.get('featured_image_url')}")
            print(f"Focus Keyword   : {seo.get('focus_keyword')} (AUTO DITENTUKAN AI)")
            print(f"Tone Terpilih   : {seo.get('detected_tone')} (AUTO DITENTUKAN AI)")
            print(f"Perspektif      : {seo.get('perspective_applied')} (AUTO DITENTUKAN AI)")
            print(f"Kategori Saran  : {seo.get('suggested_category')}")
            print(f"Skor SEO        : {qual.get('seo_score')}/100")
            print(f"Readability     : {qual.get('readability_score')}/100")
            print(f"Kemiripan       : {qual.get('similarity_percentage')}%")
            print(f"Orisinalitas    : {qual.get('originality_status')}")
            break
        else:
            print(f"Gagal: {res.text[:300]}")
    except Exception as e:
        print(f"Error: {e}")
