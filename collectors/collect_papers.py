"""arXiv 논문 수집 — RSS 피드 + 제목 한글 번역 + 누적 저장 + 중복 제거"""
import json
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from deep_translator import GoogleTranslator

RSS_FEEDS = [
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.LG",
    "https://rss.arxiv.org/rss/cs.CL",
]

def _tr(text: str) -> str:
    if not text or not text.strip():
        return text
    try:
        return GoogleTranslator(source="auto", target="ko").translate(text[:4999])
    except Exception:
        return text

def _parse_feed(url: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:12]:
            title    = (entry.get("title") or "").strip().replace("\n", " ")
            link     = entry.get("link") or ""
            arxiv_id = link.split("/abs/")[-1].strip() if "/abs/" in link else ""
            abstract = (entry.get("summary") or "").strip().replace("\n", " ")[:300]
            published = ""
            t = entry.get("published_parsed") or entry.get("updated_parsed")
            if t:
                try:
                    published = datetime(*t[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")
                except Exception:
                    pass
            authors = [a.get("name", "") for a in (entry.get("authors") or []) if a.get("name")]
            tags = [tg.get("term", "") for tg in (entry.get("tags") or [])]
            categories = [t for t in tags if t.startswith("cs.")][:3]
            if not title or not arxiv_id:
                continue
            items.append({
                "title":      title,
                "titleKo":    "",
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

    # 기존 데이터 로드 (누적 + 중복 제거용)
    existing: dict[str, dict] = {}
    if out.exists():
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
            existing = {item["arxivId"]: item for item in data.get("items", [])}
        except Exception:
            pass

    # RSS에서 새 논문 수집 (중복 제거)
    fetched: dict[str, dict] = {}
    for url in RSS_FEEDS:
        for item in _parse_feed(url):
            if item["arxivId"] not in fetched:
                fetched[item["arxivId"]] = item

    # 신규 논문 번역, 기존 논문 titleKo 없으면 번역 (최대 20건/회)
    translated = 0
    for arxiv_id, item in fetched.items():
        if arxiv_id not in existing:
            # 신규 논문
            if translated < 20:
                print(f"  번역 중: {item['title'][:40]}...")
                item["titleKo"] = _tr(item["title"])
                translated += 1
            existing[arxiv_id] = item
        # 기존 논문은 덮어쓰지 않음 (이미 번역 있을 수 있음)

    # 기존 논문 중 titleKo 없는 것 번역 (최대 10건 추가)
    for arxiv_id, item in existing.items():
        if not item.get("titleKo") and translated < 30:
            print(f"  기존 번역 중: {item['title'][:40]}...")
            item["titleKo"] = _tr(item["title"])
            translated += 1

    if not existing:
        print("[ERROR] 논문 수집 실패 — 기존 데이터 유지")
        return

    all_papers = sorted(existing.values(), key=lambda x: x.get("pubDate", ""), reverse=True)

    out.write_text(
        json.dumps({"updatedAt": _now(), "items": all_papers[:200]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 논문 {len(all_papers[:200])}건 저장 (번역 {translated}건)")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
