"""AI 채용 정보 수집 — 원티드 공개 API + 사람인"""
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AI-Jobs-Bot/1.0)",
    "Accept":     "application/json",
}

def _wanted() -> list[dict]:
    """원티드 AI/ML 직군 검색 (tag_type_ids=669: 인공지능/머신러닝)"""
    url = "https://www.wanted.co.kr/api/v4/jobs"
    params = {
        "job_sort":    "job.latest_order",
        "limit":       20,
        "offset":      0,
        "tag_type_ids": 669,
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        for item in data.get("data", []):
            position = item.get("position", {})
            company  = item.get("company", {})
            jobs.append({
                "title":   position.get("name", ""),
                "company": company.get("name", ""),
                "location": position.get("location_str", "서울"),
                "url":     f"https://www.wanted.co.kr/wd/{item.get('id', '')}",
                "tags":    [t.get("title", "") for t in position.get("tags", [])[:5]],
                "pubDate": (position.get("created_at") or "")[:10],
                "source":  "원티드",
            })
        return jobs
    except Exception as e:
        print(f"[WARN] 원티드 실패: {e}")
        return []

def _remoteok() -> list[dict]:
    """Remoteok.io — AI 원격 채용 (공개 API)"""
    try:
        resp = requests.get(
            "https://remoteok.io/api?tags=ai,machine-learning",
            headers={**HEADERS, "Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        raw = resp.json()
        jobs = []
        for item in raw[1:21]:  # 첫 번째 원소는 메타
            if not isinstance(item, dict):
                continue
            jobs.append({
                "title":   item.get("position", ""),
                "company": item.get("company", ""),
                "location": "원격",
                "url":     item.get("url", ""),
                "tags":    (item.get("tags") or [])[:5],
                "pubDate": (item.get("date") or "")[:10],
                "source":  "RemoteOK",
            })
        return jobs
    except Exception as e:
        print(f"[WARN] RemoteOK 실패: {e}")
        return []

def collect():
    jobs: list[dict] = []
    seen: set[str] = set()

    for item in _wanted() + _remoteok():
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
