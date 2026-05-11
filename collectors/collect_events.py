"""AI 행사 수집 — Festa.io 공개 API + 기존 데이터 누적"""
import json
import re
import requests
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://festa.io/",
}

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()

def _to_event(item: dict) -> dict | None:
    title = (item.get("title") or item.get("name") or "").strip()
    if not title:
        return None

    start = item.get("startAt") or item.get("startDate") or item.get("start_at") or ""
    end   = item.get("endAt")   or item.get("endDate")   or item.get("end_at")   or ""
    start_date = start[:10] if start else None
    end_date   = end[:10]   if end   else (start_date)

    loc = item.get("location") or item.get("venue") or {}
    if isinstance(loc, str):
        venue = loc or "온라인"
    elif isinstance(loc, dict):
        venue = loc.get("name") or loc.get("address") or loc.get("city") or "온라인"
    else:
        venue = "온라인"

    host = item.get("host") or item.get("organizer") or item.get("owner") or {}
    if isinstance(host, dict):
        subtitle = host.get("name") or host.get("nickname") or host.get("username") or ""
    else:
        subtitle = str(host) if host else ""

    ticket_type = (item.get("ticketType") or item.get("ticket_type") or "").upper()
    if ticket_type in ("FREE", "NONE") or not ticket_type:
        price, price_class = "무료", "price-free"
    elif ticket_type == "PAID":
        price, price_class = "유료", "price-paid"
    else:
        price, price_class = "미정", "price-tbd"

    desc = _strip_html(item.get("description") or item.get("desc") or "")[:200]

    ev_id = str(item.get("id") or item.get("slug") or item.get("eventId") or "")
    url = item.get("url") or item.get("eventUrl") or (f"https://festa.io/events/{ev_id}" if ev_id else "")
    if not url:
        return None

    return {
        "id":         f"festa_{ev_id}",
        "type":       "conference",
        "typeLabel":  "행사",
        "name":       title,
        "subtitle":   subtitle,
        "startDate":  start_date,
        "endDate":    end_date,
        "time":       "미정",
        "venue":      venue,
        "price":      price,
        "priceClass": price_class,
        "desc":       desc or title,
        "site":       url,
        "siteLabel":  "Festa.io",
        "pendingInfo": None,
        "source":     "Festa",
    }

def _festa_events() -> list[dict]:
    variants = [
        {"pageIndex": 1, "pageSize": 30, "query": "AI",    "status": "upcoming"},
        {"pageIndex": 1, "pageSize": 30, "query": "인공지능", "status": "upcoming"},
        {"page": 1,      "pageSize": 30, "query": "AI"},
    ]
    for params in variants:
        try:
            resp = requests.get(
                "https://festa.io/api/v2/events",
                params=params, headers=HEADERS, timeout=15,
            )
            print(f"[DEBUG] Festa.io status={resp.status_code}, params={params}")
            if resp.status_code != 200:
                continue
            data = resp.json()
            candidates = (
                data if isinstance(data, list)
                else data.get("events") or data.get("items")
                    or (data.get("data") or {}).get("events")
                    or data.get("results") or []
            )
            if not candidates:
                print(f"[DEBUG] 응답 키: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                continue
            result = [ev for item in candidates if (ev := _to_event(item))]
            if result:
                print(f"[OK] Festa.io {len(result)}건 수집")
                return result
        except Exception as e:
            print(f"[WARN] Festa.io 실패: {e}")
    return []

def collect():
    out = Path(__file__).parent.parent / "data" / "events.json"

    existing: dict[str, dict] = {}
    if out.exists():
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
            for item in data.get("items", []):
                key = item.get("site") or str(item.get("id", ""))
                if key:
                    existing[key] = item
        except Exception:
            pass

    new_events = _festa_events()
    added = 0
    for ev in new_events:
        key = ev.get("site") or str(ev.get("id", ""))
        if key and key not in existing:
            existing[key] = ev
            added += 1

    print(f"[OK] 행사 신규 {added}건 추가, 합계 {len(existing)}건")

    all_events = sorted(existing.values(), key=lambda x: x.get("startDate") or "9999-12-31")

    out.write_text(
        json.dumps({"updatedAt": _now(), "items": all_events}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    collect()
