"""arXiv 논문 수집 — 공식 REST API (무료, 무인증)"""
import json
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
    "atom":   "http://www.w3.org/2005/Atom",
    "arxiv":  "http://arxiv.org/schemas/atom",
}

def collect():
    try:
        resp = requests.get(ARXIV_URL, params=PARAMS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] arXiv API 실패: {e}")
        return

    root = ET.fromstring(resp.text)
    papers = []

    for entry in root.findall("atom:entry", NS):
        title = (entry.findtext("atom:title", "", NS) or "").strip().replace("\n", " ")
        raw_id = entry.findtext("atom:id", "", NS) or ""
        arxiv_id = raw_id.split("/abs/")[-1].strip()
        abstract = (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " ")[:300]
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
        categories = categories[:3]

        papers.append({
            "title":      title,
            "authors":    authors[:3],
            "arxivId":    arxiv_id,
            "url":        f"https://arxiv.org/abs/{arxiv_id}",
            "abstract":   abstract,
            "categories": categories,
            "pubDate":    published,
        })

    out = Path(__file__).parent.parent / "data" / "papers.json"
    out.write_text(
        json.dumps({"updatedAt": _now(), "items": papers}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 논문 {len(papers)}건 저장")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
