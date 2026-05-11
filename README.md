# 🧠 AI-DATA-STORAGE

> 개인 AI 정보 창고 — 행사 · 뉴스 · 논문 · 채용 · 도구를 한 곳에서

Linear + Vercel 스타일의 다크 대시보드. 정적 HTML + JSON 구조로 서버 없이 GitHub Pages에서 동작하며, GitHub Actions가 주 3회 데이터를 자동 갱신합니다.

---

## 카테고리 & 데이터 소스

| 탭 | 소스 | 방식 |
|---|---|---|
| 📅 행사 | 수동 관리 (`data/events.json`) | 직접 편집 |
| 📰 뉴스 | AI Times · TechCrunch AI · VentureBeat AI RSS | 자동 수집 |
| 📄 논문 | arXiv 공식 API (cs.AI / cs.LG / cs.CL) | 자동 수집 |
| 💼 채용 | 원티드 · RemoteOK | 자동 수집 |
| 🛠 도구 | HuggingFace Papers/Models · GitHub | 자동 수집 |

---

## 🚀 GitHub Pages 배포 (원타임 설정)

```bash
# 1. GitHub에 새 레포 생성 (Public, README 없이)

# 2. 로컬에서 push
cd C:\Users\caring\AI-DATA-STORAGE
git remote add origin https://github.com/<USERNAME>/ai-data-storage.git
git push -u origin master
```

```
3. GitHub 레포 Settings → Actions → General
   → Workflow permissions → "Read and write permissions" ✓

4. Settings → Pages
   → Source: Deploy from a branch
   → Branch: master / root → Save

5. 완료: https://<USERNAME>.github.io/ai-data-storage/
```

---

## 💻 로컬 실행

`fetch()`는 `file://` 프로토콜에서 동작하지 않으므로 로컬 서버가 필요합니다.

```bash
cd C:\Users\caring\AI-DATA-STORAGE
python -m http.server 8000
# 브라우저: http://localhost:8000
```

---

## 🔄 자동 업데이트

GitHub Actions가 **월 · 수 · 금 09:00 KST** 자동 실행:

1. `collectors/` 스크립트 4개 실행
2. `data/*.json` 갱신
3. 변경 사항 자동 커밋 & 푸시

**수동 실행:** GitHub → Actions → "AI 데이터 자동 업데이트" → **Run workflow**

---

## 📝 행사 직접 추가 / 수정

`data/events.json`의 `items` 배열에 아래 형식으로 추가:

```json
{
  "id": 6,
  "type": "conference",
  "typeLabel": "컨퍼런스",
  "name": "행사 이름",
  "subtitle": "부제목",
  "startDate": "2026-09-01",
  "endDate": "2026-09-03",
  "time": "10:00 – 18:00",
  "venue": "서울 코엑스",
  "price": "무료",
  "priceClass": "price-free",
  "desc": "행사 상세 설명.",
  "site": "https://example.com",
  "siteLabel": "공식 사이트",
  "pendingInfo": null
}
```

| 필드 | 허용 값 |
|---|---|
| `type` | `"expo"` \| `"conference"` \| `"seminar"` |
| `priceClass` | `"price-free"` \| `"price-paid"` \| `"price-tbd"` |
| `startDate` / `endDate` | `"YYYY-MM-DD"` 또는 `null` |
| `pendingInfo` | 미확정 안내 문자열 또는 `null` |

---

## 📁 파일 구조

```
AI-DATA-STORAGE/
├── .github/
│   └── workflows/
│       └── update.yml        ← 자동 수집 스케줄 (월·수·금 09:00 KST)
├── collectors/
│   ├── collect_news.py       ← RSS 뉴스 수집
│   ├── collect_papers.py     ← arXiv REST API
│   ├── collect_jobs.py       ← 원티드 + RemoteOK
│   └── collect_tools.py      ← HuggingFace + GitHub
├── data/
│   ├── events.json           ← 행사 (수동 관리, Actions가 건드리지 않음)
│   ├── news.json             ← 뉴스 (자동 갱신)
│   ├── papers.json           ← 논문 (자동 갱신)
│   ├── jobs.json             ← 채용 (자동 갱신)
│   └── tools.json            ← 도구 (자동 갱신)
├── index.html                ← 대시보드 UI (정적 HTML)
├── requirements.txt          ← Python 의존성
├── README.md                 ← 이 파일
├── CLAUDE.md                 ← Claude Code 개발 가이드
└── DESIGN.md                 ← 디자인 시스템 문서
```

---

## 🔧 로컬 수집기 직접 실행

```bash
pip install -r requirements.txt

python collectors/collect_news.py
python collectors/collect_papers.py
python collectors/collect_jobs.py
python collectors/collect_tools.py
```

---

## 참고사항

- `data/events.json`은 유일하게 **수동 관리** 파일입니다. GitHub Actions가 수정하지 않습니다.
- 나머지 4개 JSON은 수집기가 **덮어씁니다**. 직접 수정해도 다음 Actions 실행 시 초기화됩니다.
- 아카이브용 원본 파일은 `ai-events.html`로 보존되어 있습니다.
