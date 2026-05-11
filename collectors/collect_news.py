"""AI 뉴스 수집 — AI Times + GeekNews + Python KR + 누적 저장"""
import re
import json
import feedparser
from datetime import datetime, timezone
from pathlib import Path

RSS_FEEDS = [
    ("AI Times",  "https://www.aitimes.com/rss/allArticle.xml"),
    ("GeekNews",  "https://news.hada.io/rss"),
    ("Python KR", "https://discuss.python.kr/latest.rss"),
]

AI_KEYWORDS = [
    "AI", "인공지능", "머신러닝", "딥러닝", "LLM", "GPT", "생성형", "모델",
    "neural", "machine learning", "deep learning", "agent", "anthropic",
    "openai", "gemini", "claude", "chatgpt", "llama", "transformer",
    "파이썬", "python", "데이터", "자동화", "개발", "코딩",
]

NO_FILTER_SOURCES = {"Python KR", "AI Times"}

def _is_relevant(source: str, text: str) -> bool:
    if source in NO_FILTER_SOURCES:
        return True
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
    out = Path(__file__).parent.parent / "data" / "news.json"

    # 기존 데이터 로드 (누적용)
    existing: dict[str, dict] = {}
    if out.exists():
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
            existing = {item["url"]: item for item in data.get("items", [])}
        except Exception:
            pass

    new_count = 0
    for source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:25]:
                title = (entry.get("title") or "").strip()
                link  = (entry.get("link")  or "").strip()
                if not title or not link or link in existing:
                    continue

                summary = _strip_html(entry.get("summary") or "")[:300]
                if not _is_relevant(source, title + " " + summary):
                    continue

                existing[link] = {
                    "title":   title,
                    "source":  source,
                    "url":     link,
                    "pubDate": _parse_date(entry),
                    "summary": summary,
                }
                new_count += 1
        except Exception as e:
            print(f"[WARN] {source} 실패: {e}")

    print(f"[OK] 뉴스 신규 {new_count}건 추가, 합계 {len(existing)}건")

    all_articles = sorted(existing.values(), key=lambda x: x["pubDate"], reverse=True)

    out.write_text(
        json.dumps({"updatedAt": _now(), "items": all_articles[:400]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
