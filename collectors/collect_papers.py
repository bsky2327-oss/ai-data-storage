"""arXiv 논문 수집 — RSS 피드 (REST API 대비 IP 차단 없음)"""
import json
import feedparser
from datetime import datetime, timezone
from pathlib import Path

RSS_FEEDS = [
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.LG",
    "https://rss.arxiv.org/rss/cs.CL",
]

def _parse_feed(url: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:
            title = (entry.get("title") or "").strip().replace("\n", " ")
            link  = entry.get("link") or ""
            arxiv_id = link.split("/abs/")[-1].strip() if "/abs/" in link else ""
            abstract = (entry.get("summary") or "").strip().replace("\n", " ")[:300]
            published = ""
            t = entry.get("published_parsed") or entry.get("updated_parsed")
            if t:
                try:
                    published = datetime(*t[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")
                except Exception:
                    pass

            authors = []
            for a in entry.get("authors") or []:
                name = a.get("name") or ""
                if name:
                    authors.append(name)

            tags = [tag.get("term", "") for tag in (entry.get("tags") or [])]
            categories = [t for t in tags if t.startswith("cs.")][:3]

            if not title or not arxiv_id:
                continue

            items.append({
                "title":      title,
                "authors":    authors[:3],
                "arxivId":    arxiv_id,
                "url":        f"https://arxiv.org/abs/{arxiv_id}",
                "abstract":   abstract,
                "categories": categories,
                "pubDate":    published,
            })
        return items
    except Exception as e:
        print(f"[WARN] RSS 실패 ({url}): {e}")
        return []

def collect():
    out = Path(__file__).parent.parent / "data" / "papers.json"

    papers: list[dict] = []
    seen: set[str] = set()

    for url in RSS_FEEDS:
        for item in _parse_feed(url):
            if item["arxivId"] not in seen:
                seen.add(item["arxivId"])
                papers.append(item)

    if not papers:
        print("[ERROR] 논문 수집 실패 — 기존 데이터 유지")
        return

    papers.sort(key=lambda x: x.get("pubDate", ""), reverse=True)

    out.write_text(
        json.dumps({"updatedAt": _now(), "items": papers[:40]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 논문 {len(papers[:40])}건 저장")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
