# Design System — AI Events Page

## 테마 개요

다크 테마 기반의 정보 제공형 웹 페이지. 신뢰감·가독성·시각적 위계를 목표로 함.

---

## 색상 팔레트

| 토큰 | 값 | 용도 |
|------|----|------|
| `--bg` | `#0f1117` | 페이지 배경 |
| `--surface` | `#1a1d27` | 카드 배경 |
| `--surface2` | `#22263a` | 카드 내부 정보 블록 |
| `--border` | `#2e3350` | 테두리 |
| `--accent` | `#4f8ef7` | 주 강조색 (컨퍼런스, 링크) |
| `--accent2` | `#7c5cfc` | 보조 강조색 (박람회) |
| `--green` | `#22c55e` | 세미나 / 무료 / 예정 뱃지 |
| `--yellow` | `#f59e0b` | 경고 / 정보 미발표 |
| `--text` | `#e2e8f0` | 본문 |
| `--text2` | `#94a3b8` | 보조 텍스트 |

### 행사 유형별 액센트 색상

| 유형 | 색상 | 토큰 |
|------|------|------|
| 박람회 | `#7c5cfc` (보라) | `--clr-expo` |
| 컨퍼런스 | `#4f8ef7` (파랑) | `--clr-conf` |
| 세미나/심포지엄 | `#22c55e` (초록) | `--clr-semi` |

---

## 적용된 개선 3가지

### 1. 좌측 컬러 액센트 바
카드 왼쪽에 행사 유형별 색상의 4px 세로 바를 배치. 목록을 빠르게 스캔할 때 유형을 즉시 식별 가능.

```css
.event-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
}
.event-card[data-type="expo"]::before       { background: #7c5cfc; }
.event-card[data-type="conference"]::before  { background: #4f8ef7; }
.event-card[data-type="seminar"]::before     { background: #22c55e; }
```

### 2. 헤더 글래스모피즘
헤더를 반투명 + blur 처리하여 스크롤 시 뒤 콘텐츠가 비쳐 보이는 깊이감 연출.

```css
header {
  background: rgba(13, 17, 34, 0.65);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.4);
}
```

로딩 오버레이에도 동일 기법 적용:
```css
.loading-overlay {
  background: rgba(15, 17, 23, 0.55);
  backdrop-filter: blur(8px);
}
```

### 3. 호버 시 그라디언트 글로우
`border-color` 변경 대신 `box-shadow`로 글로우 효과. 행사 유형 색상을 유지하면서 입체감 추가.

```css
/* 컨퍼런스 (기본) */
.event-card:hover {
  transform: translateY(-3px);
  box-shadow:
    0 0 0 1px #4f8ef7,
    0 8px 32px rgba(79, 142, 247, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.3);
}

/* 박람회 */
.event-card[data-type="expo"]:hover {
  box-shadow:
    0 0 0 1px #7c5cfc,
    0 8px 32px rgba(124, 92, 252, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.3);
}
```

---

## 레이아웃 원칙

- **최대 너비**: `960px`, 중앙 정렬
- **카드 그리드**: 단일 컬럼 (`grid-template-columns: 1fr`) — 정보 밀도가 높아 2열 시 가독성 저하
- **정보 블록**: `auto-fill minmax(190px, 1fr)` — 반응형으로 2~4열 자동 조정
- **카드 내 좌측 패딩**: `28px` (액센트 바 4px + 여백)

---

## 타이포그래피

- **폰트**: Pretendard → Apple SD Gothic Neo → Noto Sans KR (시스템 폰트 폴백)
- **제목**: `1.08rem / 700 weight`
- **본문**: `0.84–0.88rem / 1.65–1.7 line-height`
- **레이블**: `0.7rem / uppercase / letter-spacing: 0.1em`

---

## 인터랙션 패턴

| 요소 | 동작 |
|------|------|
| 카드 호버 | `translateY(-3px)` + 유형별 글로우 |
| 새로고침 버튼 | 클릭 → 스피너 애니메이션 → 0.9초 후 카드 fadeIn 재생 |
| 카드 등장 | `fadeIn` 애니메이션, 카드별 60ms delay로 순차 등장 |
| 필터 전환 | 즉시 DOM 재렌더 (애니메이션 없이 빠르게) |
| 링크 호버 | `box-shadow: 0 0 0 1px accent` (outline 대신 shadow 활용) |

---

## 재사용 가이드

동일 디자인을 다른 정보형 페이지(채용공고, 행사 외 목록 등)에 적용할 때 변경 최소화 포인트:

1. `--clr-*` 토큰만 교체 → 유형별 색상 변경
2. `EVENTS` 배열 교체 → 데이터 변경
3. `filter-btn` `data-filter` 값 → 카테고리 변경
4. `info-grid` 내 `info-item` 개수·레이블 → 표시 필드 변경
