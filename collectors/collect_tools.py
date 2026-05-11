"""AI 도구/모델 출시 정보 수집 — HuggingFace + GitHub Trending"""
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-Tools-Bot/1.0)"}

def _hf_daily_papers() -> list[dict]:
    """HuggingFace 커뮤니티 선정 일일 주요 논문·모델"""
    try:
        resp = requests.get("https://huggingface.co/api/daily_papers", headers=HEADERS, timeout=15)
        resp.raise_for_status()
        items = []
        for paper in resp.json()[:15]:
            p = paper.get("paper", {})
            items.append({
                "name":    p.get("title", ""),
                "desc":    (p.get("summary") or "")[:200],
                "url":     f"https://huggingface.co/papers/{p.get('id', '')}",
                "tags":    [],
                "source":  "HuggingFace Papers",
                "pubDate": (paper.get("publishedAt") or "")[:10],
            })
        return items
    except Exception as e:
        print(f"[WARN] HF Daily Papers 실패: {e}")
        return []

def _hf_trending_models() -> list[dict]:
    """HuggingFace 최신 인기 모델 (text-generation)"""
    url = "https://huggingface.co/api/models"
    params = {"sort": "likes7d", "direction": -1, "limit": 10, "filter": "text-generation"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        items = []
        for m in resp.json():
            mid = m.get("modelId") or m.get("id", "")
            items.append({
                "name":    mid,
                "desc":    f"🤗 HuggingFace 모델 | 좋아요(7일): {m.get('likes', 0)}",
                "url":     f"https://huggingface.co/{mid}",
                "tags":    (m.get("tags") or [])[:4],
                "source":  "HuggingFace Models",
                "pubDate": (m.get("createdAt") or "")[:10],
            })
        return items
    except Exception as e:
        print(f"[WARN] HF Models 실패: {e}")
        return []

def _github_trending_ai() -> list[dict]:
    """GitHub 최신 AI 관련 레포 (공식 Search API)"""
    url = "https://api.github.com/search/repositories"
    params = {
        "q":        "topic:artificial-intelligence pushed:>2026-01-01",
        "sort":     "updated",
        "order":    "desc",
        "per_page": 10,
    }
    try:
        resp = requests.get(url, params=params, headers={**HEADERS, "Accept": "application/vnd.github+json"}, timeout=15)
        resp.raise_for_status()
        items = []
        for repo in resp.json().get("items", []):
            items.append({
                "name":    repo.get("full_name", ""),
                "desc":    (repo.get("description") or "")[:150],
                "url":     repo.get("html_url", ""),
                "tags":    (repo.get("topics") or [])[:4],
                "source":  "GitHub",
                "pubDate": (repo.get("pushed_at") or "")[:10],
            })
        return items
    except Exception as e:
        print(f"[WARN] GitHub 실패: {e}")
        return []

def collect():
    tools: list[dict] = []
    seen: set[str] = set()

    for item in _hf_daily_papers() + _hf_trending_models() + _github_trending_ai():
        url = item.get("url", "")
        if url and url not in seen and item.get("name"):
            seen.add(url)
            tools.append(item)

    tools.sort(key=lambda x: x.get("pubDate", ""), reverse=True)

    out = Path(__file__).parent.parent / "data" / "tools.json"
    out.write_text(
        json.dumps({"updatedAt": _now(), "items": tools[:40]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 도구/모델 {len(tools[:40])}건 저장")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
