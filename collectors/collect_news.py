"""AI 뉴스 수집 — RSS 기반 (무료, 무인증)"""
import re
import json
import feedparser
from datetime import datetime, timezone
from pathlib import Path

RSS_FEEDS = [
    ("AI Times",      "https://www.aitimes.com/rss/allArticle.xml"),
    ("블로터",         "https://www.bloter.net/feed"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("VentureBeat AI","https://venturebeat.com/ai/feed/"),
]

AI_KEYWORDS = ["AI", "인공지능", "머신러닝", "딥러닝", "LLM", "GPT", "생성형",
               "모델", "neural", "machine learning", "deep learning", "agent", "anthropic", "openai", "gemini"]

def _is_ai(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in AI_KEYWORDS)

def _parse_date(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                pass
    return ""

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()

def collect():
    articles = []
    seen_urls: set[str] = set()

    for source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:15]:
                title = (entry.get("title") or "").strip()
                link  = (entry.get("link")  or "").strip()
                if not title or not link or link in seen_urls:
                    continue
                if not _is_ai(title) and not _is_ai(entry.get("summary") or ""):
                    continue
                seen_urls.add(link)
                summary = _strip_html(entry.get("summary") or "")[:200]
                articles.append({
                    "title":   title,
                    "source":  source,
                    "url":     link,
                    "pubDate": _parse_date(entry),
                    "summary": summary,
                })
        except Exception as e:
            print(f"[WARN] {source} 실패: {e}")

    articles.sort(key=lambda x: x["pubDate"], reverse=True)

    out = Path(__file__).parent.parent / "data" / "news.json"
    out.write_text(
        json.dumps({"updatedAt": _now(), "items": articles[:40]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 뉴스 {len(articles[:40])}건 저장")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
