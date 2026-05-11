"""GitHub AI 레포 수집 — 누적 저장 + 트렌딩 감지 + 한국어 번역"""
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from deep_translator import GoogleTranslator

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AI-Tools-Bot/1.0)",
    "Accept":     "application/vnd.github+json",
}

# (쿼리, 가져올 수)
GITHUB_QUERIES = [
    ("topic:artificial-intelligence stars:>200 pushed:>2025-01-01", 10),
    ("topic:llm stars:>100 pushed:>2025-01-01",                     10),
    ("topic:large-language-model stars:>100",                        8),
    ("topic:generative-ai stars:>100 pushed:>2025-01-01",           8),
    ("topic:machine-learning stars:>500 pushed:>2025-01-01",         8),
    ("topic:deep-learning stars:>300 pushed:>2025-01-01",            6),
]

def _tr(text: str) -> str:
    if not text or not text.strip():
        return text
    try:
        return GoogleTranslator(source="auto", target="ko").translate(text[:4999])
    except Exception:
        return text

def _is_trending(item: dict) -> bool:
    pub   = item.get("pubDate", "")
    stars = item.get("stars", 0)
    if pub and stars >= 500:
        try:
            days_old = (datetime.now() - datetime.strptime(pub, "%Y-%m-%d")).days
            return days_old <= 60
        except Exception:
            pass
    return False

def _fetch(query: str, limit: int) -> list[dict]:
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": limit},
            headers=HEADERS, timeout=15,
        )
        resp.raise_for_status()
        repos = []
        for repo in resp.json().get("items", []):
            repos.append({
                "name":     repo.get("full_name", ""),
                "desc":     (repo.get("description") or "")[:300],
                "url":      repo.get("html_url", ""),
                "tags":     (repo.get("topics") or [])[:5],
                "source":   "GitHub",
                "pubDate":  (repo.get("created_at") or "")[:10],
                "stars":    repo.get("stargazers_count", 0),
                "language": repo.get("language") or "",
                "pushed":   (repo.get("pushed_at") or "")[:10],
            })
        return repos
    except Exception as e:
        print(f"[WARN] GitHub 쿼리 실패 ({query[:40]}): {e}")
        return []

def collect():
    out = Path(__file__).parent.parent / "data" / "tools.json"

    # 기존 데이터 로드 (누적용)
    existing: dict[str, dict] = {}
    if out.exists():
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
            existing = {item["url"]: item for item in data.get("items", [])}
        except Exception:
            pass

    # GitHub에서 최신 레포 수집
    seen: set[str] = set()
    new_repos: list[dict] = []
    for query, limit in GITHUB_QUERIES:
        for repo in _fetch(query, limit):
            if repo["url"] not in seen:
                seen.add(repo["url"])
                new_repos.append(repo)

    new_count = 0
    for repo in new_repos:
        url = repo["url"]
        if url in existing:
            # 별점·최신화 날짜만 업데이트, 기존 한국어 번역 유지
            existing[url]["stars"]  = repo["stars"]
            existing[url]["pushed"] = repo["pushed"]
        else:
            # 신규 레포: 설명 번역
            if repo["desc"]:
                print(f"  번역 중: {repo['name'][:40]}")
                repo["desc"] = _tr(repo["desc"])
            existing[url] = repo
            new_count += 1

    print(f"[OK] GitHub 신규 {new_count}건 추가, 합계 {len(existing)}건")

    all_tools = list(existing.values())

    # trending 필드 설정
    for item in all_tools:
        item["trending"] = _is_trending(item)

    # 정렬: 트렌딩 먼저, 그 다음 별점 순
    trending = sorted([t for t in all_tools if t["trending"]],     key=lambda x: x.get("stars", 0), reverse=True)
    normal   = sorted([t for t in all_tools if not t["trending"]], key=lambda x: x.get("stars", 0), reverse=True)
    result   = trending + normal

    out.write_text(
        json.dumps({"updatedAt": _now(), "items": result[:300]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 도구 {len(result[:300])}건 저장 (트렌딩 {len(trending)}건)")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
