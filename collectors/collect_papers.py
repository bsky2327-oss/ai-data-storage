"""arXiv 논문 수집 — 공식 REST API (무료, 무인증)"""
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ARXIV_URL = "https://export.arxiv.org/api/query"
PARAMS = {
    "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
    "sortBy":       "lastUpdatedDate",
    "sortOrder":    "descending",
    "max_results":  25,
}
NS = {
    "atom":  "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

def _fetch(retries: int = 3) -> requests.Response | None:
    """타임아웃 60초, 최대 3회 재시도"""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                ARXIV_URL, params=PARAMS,
                timeout=60,
                headers={"User-Agent": "Mozilla/5.0 (AI-Data-Storage/1.0)"},
            )
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"[WARN] arXiv 시도 {attempt}/{retries} 실패: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)  # 5초, 10초 대기 후 재시도
    return None

def collect():
    out = Path(__file__).parent.parent / "data" / "papers.json"

    resp = _fetch()
    if resp is None:
        print("[ERROR] arXiv API 최종 실패 — 기존 데이터 유지")
        return  # 기존 파일 보존, 덮어쓰지 않음

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        print(f"[ERROR] XML 파싱 실패: {e} — 기존 데이터 유지")
        return

    papers = []
    for entry in root.findall("atom:entry", NS):
        title     = (entry.findtext("atom:title", "", NS) or "").strip().replace("\n", " ")
        raw_id    = entry.findtext("atom:id", "", NS) or ""
        arxiv_id  = raw_id.split("/abs/")[-1].strip()
        abstract  = (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " ")[:300]
        published = (entry.findtext("atom:published", "", NS) or "")[:10]

        authors = [
            a.findtext("atom:name", "", NS)
            for a in entry.findall("atom:author", NS)
        ]

        categories = []
        pc = entry.find("arxiv:primary_category", NS)
        if pc is not None:
            categories.append(pc.get("term", ""))
        for c in entry.findall("atom:category", NS):
            t = c.get("term", "")
            if t.startswith("cs.") and t not in categories:
                categories.append(t)

        if not title or not arxiv_id:
            continue

        papers.append({
            "title":      title,
            "authors":    authors[:3],
            "arxivId":    arxiv_id,
            "url":        f"https://arxiv.org/abs/{arxiv_id}",
            "abstract":   abstract,
            "categories": categories[:3],
            "pubDate":    published,
        })

    out.write_text(
        json.dumps({"updatedAt": _now(), "items": papers}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 논문 {len(papers)}건 저장")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
