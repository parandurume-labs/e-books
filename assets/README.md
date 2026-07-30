# 공용 디자인 시스템 v2.2

이 폴더의 CSS와 JS를 **4권의 e-book과 루트 컬렉션 페이지가 함께** 씁니다.
새 책을 만들 때 스타일을 복사하지 마세요. 여기를 참조하면 됩니다.

```
assets/
├── css/book.css   구조 · 조판 · 컴포넌트 전부
└── js/book.js     사이드바 · 다크모드 · 진행바 · 이 장에서 · ⌘K 검색
                + 리더 기능(복사·이어보기·진행률·글자 크기·키보드)
```

## 설계 방향

| 축 | 결정 | 이유 |
|---|---|---|
| 구조 | Vercel·Mintlify 계열 3단 (사이드바 + 본문 + 이 장에서) | 14~20장 규모에서 찾아 읽기가 가능해야 한다 |
| 조판 | 본문 42rem(≈640px), 유동 타입 스케일, 행간 1.8 | 900px 폭 16px는 한글 장문에 한 줄 100자가 넘는다 |
| 글꼴 | Pretendard Variable (한 파일, 9굵기) | Noto Sans KR 다중 파일보다 빠르고 영문(Inter 기반)이 자연스럽다 |
| 질감 | 그림자 없음. 헤어라인과 색조 레이어로만 구분 | 그라디언트·부유 도형은 2021년 랜딩페이지 인상을 준다 |
| 아이콘 | 인라인 SVG 선 아이콘 | 이모지는 플랫폼마다 다르게 렌더링되고 톤이 흔들린다 |
| 색 | 따뜻한 뉴트럴 + 책별 강조색 1개 | 컬렉션 정체성(크림 계열)을 유지하면서 책을 구분한다 |
| 표제 (v2.1) | Noto Serif KR, 본문은 Pretendard 유지 | 장문 표제에 세리프를 쓰면 책의 인상이 생긴다. 본문 세리프는 화면에서 오히려 피로하다 |
| 도판 (v2.1) | 글줄 42rem, 표·그림은 48rem까지 | 5~6열 표와 SVG 다이어그램이 글줄 폭에 갇히면 못 읽는다 |
| 리더 (v2.1) | 복사·이어보기·진행률·글자 크기 | 잘 조판된 웹 문서와 e-book 을 가르는 것은 조판이 아니라 이 장치들이다 |

## 새 책 추가 절차

1. 폴더를 만들고 `chapters/`, `css/` 를 둡니다.
2. `css/theme.css` 에 강조색 4개만 정의합니다 (라이트 + 다크).

```css
:root {
  --accent: #0F766E;       /* 링크·강조·번호 */
  --accent-ink: #0B5A54;   /* 강조 텍스트 (대비 확보용) */
  --accent-tint: #E4F2EF;  /* 강조 배경 */
  --accent-line: #A8D8D0;  /* 강조 테두리 */
}
[data-theme="dark"] { /* 다크 모드용 4개 */ }
```

3. `index.html` 과 챕터 페이지의 `<head>` 에 다음을 넣습니다.

```html
<link rel="stylesheet" href="../assets/css/book.css">   <!-- 챕터는 ../../ -->
<link rel="stylesheet" href="css/theme.css">            <!-- 챕터는 ../css/ -->
<script>try{var t=localStorage.getItem('pdm-ebook-theme');if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.setAttribute('data-theme','dark')}catch(e){}</script>
```

4. `</body>` 앞에 `<script src="../assets/js/book.js"></script>` (챕터는 `../../`).
5. 챕터 페이지 골격은 기존 책의 아무 챕터나 복사해 쓰면 됩니다.

## 본문 컴포넌트

| 클래스 | 용도 |
|---|---|
| `.callout` / `.callout-tip` | 핵심 메시지 |
| `.pitfall` | 실제로 걸리는 함정 (경고색 좌측 괘선) |
| `.case-box` | 사례 |
| `.fun-box` | 쉬운 비유 |
| `.exercise-box` | 직접 해보기 |
| `.recap-box` | 잠깐 정리 (위아래 괘선) |
| `.next-teaser` | 다음 장 예고 |
| `ol.steps` | 번호 단계 (좌측 타임라인) |
| `ul.checklist` | 체크리스트 |
| `.file-tree` | 폴더 구조 (`<span class="comment">` 로 주석) |
| `.prompt-example` | 나쁜 예 / 좋은 예 대비 |
| `.illustration` | 인라인 SVG 또는 이미지 + 캡션 |

## 조판 토큰

| 토큰 | 값 | 의미 |
|---|---|---|
| `--measure` | `42rem` | **글줄 폭.** 한글 한 줄 40자 안팎. 가독성 근거라 건드리지 않습니다 |
| `--bleed` | `6rem` | 표·그림만 글줄보다 이만큼 넓게 나갈 수 있습니다 |
| `--reader-scale` | `1` | 리더의 A⁻ A A⁺ 가 이 값만 바꿉니다 (0.94 / 1 / 1.09) |
| `--font-display` | `Noto Serif KR` | 표제 전용. 본문은 `--font-sans` |

`--measure` 보다 넓게 나갈 요소를 추가하려면 `@media (min-width: 1280px)` 안의
「글줄은 --measure, 그림과 표는 칸 전체」 블록에 선택자를 더하면 됩니다.

## 산세리프 표제로 되돌리려면

책의 `theme.css` 에 한 줄만 넣으면 됩니다.

```css
:root { --font-display: var(--font-sans); --display-weight: 600; }
```

## 자동으로 처리되는 것

- **목차 카드 번호** — 카드의 이모지를 CSS 카운터가 대체합니다. HTML을 고칠 필요 없습니다.
- **깨진 일러스트** — 이미지 로드 실패 시 해당 `<figure>` 를 JS가 제거합니다.
- **다크 모드 유지** — `localStorage` 에 저장되어 페이지를 넘어가도 유지됩니다.
- **이 장에서** — 본문 `h2`/`h3` 를 읽어 자동 생성하고 스크롤을 따라 강조합니다. 표제가 3개 미만이면 숨깁니다.
- **⌘K 검색** — 사이드바 목차를 색인해 즉시 이동합니다.
- **장 오프너** — 사이드바에서 부 이름을, 목차 개수에서 「19장 중 14번째」를 뽑아 붙입니다.
- **읽는 시간** — `.reading-time` 이 없는 책은 본문 글자수 ÷ 500자/분으로 추정해 넣습니다.
- **복사 버튼** — `pre` 와 `.file-tree` 를 `.code-wrap` 으로 감싸고 버튼을 답니다.
  클립보드 API 가 거부되면 `execCommand` 폴백을 한 번 더 시도합니다.
- **표 가로 스크롤** — `.table-wrap > .table-scroll > table` 로 감쌉니다.
  4열 이상이면 `열수 × 8.5rem`(최대 40rem)을 최소 폭으로 줘서 좁은 화면에서 셀이 뭉개지지 않게 합니다.
- **이어보기** — 장별 스크롤 %를 `localStorage` 에 저장하고, 5~92% 구간이면 알약을 띄웁니다. 30개까지만 보관합니다.
- **키보드** — `←` `→` 로 이전·다음 장. 하단 `.chapter-nav` 링크를 그대로 씁니다.
- **언어 스위처** — `link[rel="alternate"][hreflang]` 가 있는 페이지에만 `KO / EN` 을 만듭니다.
  대응 파일이 없으면 아예 안 생기므로 404 가 나지 않습니다.
- **UI 언어** — `<html lang>` 으로 문자열 사전(`STRINGS.ko` / `STRINGS.en`)을 고릅니다.
  새 문자열을 추가할 때 **양쪽에 다 넣으세요.** 한쪽만 넣으면 그 언어에서 `undefined` 가 뜹니다.

## 주의 — 건드리면 깨지는 것

| 규칙 | 왜 있는지 |
|---|---|
| `.chapter-shell .chapter-content { width: 100% }` | `width:auto` 면 줄바꿈 안 되는 긴 코드 한 줄이 그리드 칸을 뚫고 **우측 레일 위로 본문이 겹칩니다.** `min-width:0` 으로는 크로미움에서 안 막힙니다 |
| `@media (min-width:1024px) .mobile-header { margin-left: var(--sidebar-w) }` | 없으면 **책 제목이 사이드바 뒤에 완전히 가립니다** |
| `.chapter-content table { display:block; overflow-x:auto }` | JS 가 없을 때의 안전망. 없으면 열 많은 표가 **페이지를 가로로 밀어냅니다** |
| `.chapter-content th, td { word-break: keep-all }` | 없으면 좁은 화면에서 한글이 **한 글자씩 세로로 쌓입니다** |
