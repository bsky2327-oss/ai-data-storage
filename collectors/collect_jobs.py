"""AI 채용 정보 수집 — Remotive + Jobicy (공개 API, 해외 IP 차단 없음)
원티드는 GitHub Actions의 해외 IP에서 403 차단되어 제외.
"""
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AI-Jobs-Bot/1.0)",
    "Accept":     "application/json",
}

def _remotive() -> list[dict]:
    """Remotive — 공식 공개 API (인증 불필요)"""
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev", "search": "AI", "limit": 25},
            headers=HEADERS, timeout=20,
        )
        resp.raise_for_status()
        jobs = []
        for item in resp.json().get("jobs", []):
            tags = item.get("tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            jobs.append({
                "title":    item.get("title", ""),
                "company":  item.get("company_name", ""),
                "location": item.get("candidate_required_location") or "원격",
                "url":      item.get("url", ""),
                "tags":     [t for t in tags[:5] if t],
                "pubDate":  (item.get("publication_date") or "")[:10],
                "source":   "Remotive",
            })
        return jobs
    except Exception as e:
        print(f"[WARN] Remotive 실패: {e}")
        return []

def _jobicy() -> list[dict]:
    """Jobicy — 공식 공개 API (인증 불필요)"""
    try:
        resp = requests.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"count": 20, "tag": "ai"},
            headers=HEADERS, timeout=20,
        )
        resp.raise_for_status()
        jobs = []
        for item in resp.json().get("jobs", []):
            jobs.append({
                "title":    item.get("jobTitle", ""),
                "company":  item.get("companyName", ""),
                "location": item.get("jobGeo") or "원격",
                "url":      item.get("url", ""),
                "tags":     [item.get("jobCategory", ""), item.get("jobType", "")],
                "pubDate":  (item.get("pubDate") or "")[:10],
                "source":   "Jobicy",
            })
        return jobs
    except Exception as e:
        print(f"[WARN] Jobicy 실패: {e}")
        return []

def collect():
    jobs: list[dict] = []
    seen: set[str] = set()

    for item in _remotive() + _jobicy():
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            jobs.append(item)

    jobs.sort(key=lambda x: x.get("pubDate", ""), reverse=True)

    out = Path(__file__).parent.parent / "data" / "jobs.json"
    out.write_text(
        json.dumps({"updatedAt": _now(), "items": jobs[:40]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 채용 {len(jobs[:40])}건 저장")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
