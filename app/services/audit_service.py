import re
import logging
from typing import List, Dict, Any

from app.services.technical_service import clean_text

logger = logging.getLogger(__name__)


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Menghitung tingkat kemiripan teks menggunakan Jaccard word-level similarity."""
    w1 = set(clean_text(text1).split())
    w2 = set(clean_text(text2).split())
    if not w1 or not w2:
        return 0.0
    intersection = len(w1.intersection(w2))
    union = len(w1.union(w2))
    return round((intersection / union) * 100, 1) if union > 0 else 0.0


def detect_keyword_cannibalization(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Mendeteksi benturan kata kunci (Keyword Cannibalization) antar artikel di portal BorneoFlash."""
    cannibalized_pairs = []
    total_articles = len(articles)

    for i in range(total_articles):
        for j in range(i + 1, total_articles):
            a1 = articles[i]
            a2 = articles[j]

            kw1 = (a1.get("focus_keyword") or "").strip().lower()
            kw2 = (a2.get("focus_keyword") or "").strip().lower()

            title1 = (a1.get("title") or "").strip()
            title2 = (a2.get("title") or "").strip()

            is_exact_kw_clash = bool(kw1 and kw2 and kw1 == kw2)
            title_similarity = calculate_jaccard_similarity(title1, title2)

            if is_exact_kw_clash or title_similarity >= 65.0:
                severity = "Kritis" if is_exact_kw_clash and title_similarity >= 60.0 else "Tinggi" if is_exact_kw_clash else "Sedang"
                cannibalized_pairs.append({
                    "severity": severity,
                    "focus_keyword": kw1 if is_exact_kw_clash else f"'{kw1}' vs '{kw2}'",
                    "title_similarity_percent": title_similarity,
                    "article_1": {
                        "id": a1.get("id"),
                        "title": title1,
                        "url": a1.get("url")
                    },
                    "article_2": {
                        "id": a2.get("id"),
                        "title": title2,
                        "url": a2.get("url")
                    },
                    "recommendation": (
                        "Kedua artikel memiliki kata kunci fokus persis sama! Bedakan sudut pandang "
                        "atau lakukan kanonikalisasi / penggabungan naskah agar ranking Google tidak terpecah."
                        if is_exact_kw_clash
                        else f"Judul kedua artikel memiliki kemiripan kata {title_similarity}%. Pertimbangkan membedakan subjek atau lokasi."
                    )
                })

    return {
        "status": "success",
        "total_articles_audited": total_articles,
        "clash_detected_count": len(cannibalized_pairs),
        "cannibalization_risks": cannibalized_pairs
    }
