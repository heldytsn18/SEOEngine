import json
from typing import Dict, Any

from app.schemas.seo_schema import SchemaJSONLDRequest


def generate_newsarticle_jsonld(data: SchemaJSONLDRequest) -> Dict[str, Any]:
    """Generate struktur NewsArticle Schema.org JSON-LD yang valid untuk Google News."""
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": data.title[:110],  # Google rekomendasikan max 110 karakter
        "description": data.description,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": data.article_url
        },
        "author": {
            "@type": "Person",
            "name": data.author_name
        },
        "publisher": {
            "@type": "Organization",
            "name": data.publisher_name,
            "logo": {
                "@type": "ImageObject",
                "url": data.publisher_logo_url
            }
        },
        "datePublished": data.date_published,
        "url": data.article_url
    }

    if data.date_modified:
        schema["dateModified"] = data.date_modified

    if data.image_url:
        schema["image"] = {
            "@type": "ImageObject",
            "url": data.image_url
        }

    return schema


def render_html_snippet(schema: Dict[str, Any]) -> str:
    """Render JSON-LD ke HTML snippet siap paste."""
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
