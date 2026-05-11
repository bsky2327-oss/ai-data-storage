# AI-DATA-STORAGE — Claude Code 개발 가이드

## 프로젝트 개요

개인 AI 정보 창고. 정적 `index.html` + `data/*.json` 구조.
GitHub Actions가 `data/` 폴더를 주 3회 자동 갱신.
서버 없이 GitHub Pages에서 동작.

---

## 아키텍처 요약

```
index.html  ←fetch()←  data/*.json  ←덮어씀←  collectors/*.py
                              ↑
                     data/events.json (수동 관리, 예외)
```

- `index.html`: 탭 전환 시 해당 JSON을 fetch → 렌더링
- `cache` 객체로 한 번 로드한 데이터 메모리 보존 (새로고침 전까지)
- `--accent` CSS 변수를 탭별로 동적 변경 → 색상 테마 전환

---

## 핵심 파일

| 파일 | 역할 | 수정 빈도 |
|------|------|----------|
| `index.html` | 5탭 대시보드 UI (CSS + JS 인라인) | UI 변경 시 |
| `data/events.json` | 행사 데이터 (**수동 편집**) | 행사 추가/삭제 시 |
| `collectors/collect_news.py` | RSS → news.json | 소스 추가 시 |
| `collectors/collect_papers.py` | arXiv API → papers.json | 카테고리 변경 시 |
| `collectors/collect_jobs.py` | 원티드/RemoteOK → jobs.json | API 변경 시 |
| `collectors/collect_tools.py` | HuggingFace/GitHub → tools.json | 소스 추가 시 |
| `.github/workflows/update.yml` | 자동화 스케줄 | 주기 변경 시 |

---

## 작업 규칙

### 절대 하지 말 것
- `data/events.json` 이외의 JSON 파일을 수동으로 수정하지 말 것 (수집기가 덮어씀)
- `index.html`에서 `fetch()` URL 경로를 바꾸지 말 것 (`data/` 하위 고정)
- 수집기가 실패해도 기존 파일을 삭제하거나 빈 파일로 덮어쓰지 말 것

### 로컬 테스트
```bash
# HTML은 반드시 HTTP 서버 통해 실행 (file:// 불가)
python -m http.server 8000

# 수집기 개별 실행
python collectors/collect_news.py
```

---

## 행사 데이터 추가

`data/events.json` → `items` 배열에 추가:

```json
{
  "id": <다음 번호>,
  "type": "expo" | "conference" | "seminar",
  "typeLabel": "박람회" | "컨퍼런스" | "세미나",
  "name": "행사 전체 이름",
  "subtitle": "주관사 또는 부제목",
  "startDate": "YYYY-MM-DD",   // null 허용 (일정 미확정)
  "endDate": "YYYY-MM-DD",     // null 허용
  "time": "10:00 – 18:00",
  "venue": "장소명",
  "price": "가격 설명",
  "priceClass": "price-free" | "price-paid" | "price-tbd",
  "desc": "행사 설명 (2~3문장)",
  "site": "https://...",
  "siteLabel": "공식 사이트",
  "pendingInfo": null           // 또는 미확정 안내 문자열
}
```

지난 행사(endDate < 오늘)는 UI에서 자동 숨김.

---

## 수집기 구조

모든 수집기는 동일한 출력 형식을 따름:

```python
out.write_text(
    json.dumps({"updatedAt": _now(), "items": [...]}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

**실패 시 처리**: 수집 실패 시 기존 파일을 유지 (덮어쓰지 않음). 빈 `items`가 아닌 이전 데이터 보존.

---

## 새 수집 소스 추가 방법

1. 해당 수집기 파일 수정 (예: `collect_news.py` → `RSS_FEEDS` 리스트에 추가)
2. `index.html` → 해당 탭의 `filters` 배열에 소스명 필터 추가
3. 로컬에서 수집기 실행 후 JSON 확인
4. `git add data/ index.html && git commit`

---

## 디자인 수정

`DESIGN.md` 참고. CSS 변수로 관리:

```css
--c-events: #3b82f6;   /* 행사 탭 */
--c-news:   #f59e0b;   /* 뉴스 탭 */
--c-papers: #8b5cf6;   /* 논문 탭 */
--c-jobs:   #10b981;   /* 채용 탭 */
--c-tools:  #f97316;   /* 도구 탭 */
```

탭 전환 시 `--accent`가 동적으로 변경됨.

---

## GitHub Actions 수동 트리거

```
GitHub → Actions 탭 → "AI 데이터 자동 업데이트" → Run workflow
```
