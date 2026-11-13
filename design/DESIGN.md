# Sleeby 챗봇 디자인 시스템

출처: `design/sleepy-landing.html`(객실의 밤: 훈연 월넛 바닥, 리넨 글자, 스탠드 조명 하나)에서 토큰을 추출했다.
구현: `frontend/src/styles/tokens.css`(원시 값은 이 파일에만), `base.css`, `components.css`.
규칙: 모든 화면은 `var(--...)` 토큰만 쓴다. `cd frontend; npm run lint`(= oxlint + `lint:design`)가 위반을 막는다.

## 1. 색상

| 역할 | 토큰 | 값 |
|---|---|---|
| 페이지 배경 | `--color-bg-page` | #15110d (walnut) |
| 벽·카드 배경 | `--color-bg-wall`, `--color-bg-surface`, `--color-bg-surface-raised` | #1c1713, #261e18, #31271f |
| 입력창 배경 | `--color-bg-field` | #0f0c0a |
| 글자 | `--color-text`, `-secondary`, `-muted` | #ede4d3, #c4b7a2, #9c8f7c |
| 강조(스탠드 불빛) | `--color-accent`, `-hover`, `--color-on-accent` | #e8b46a, #f4cc8e, #20150a |
| 테두리 | `--color-border-subtle`, `--color-border`, `--color-border-strong` | 리넨 9%, 황동 34%, 황동 60% |
| 오류 | `--color-danger` | #e58a7a (레퍼런스에 없음, 앱 오류 표시용 추가) |

채움은 램프 색 투명도 단계(`--fill-lamp-faint` 4%, `subtle` 5%, `soft` 8%, `medium` 14%, `strong` 24%)와 리넨(`--fill-linen-*`)을 쓴다.
레퍼런스의 #0E0B09, #0F0C0A는 #0f0c0a 하나로 통합했다.

## 2. 타이포그래피

- 서체: 제목 `--font-display`(Hahmlet), 본문 `--font-sans`(Pretendard Variable), 코드 `--font-mono`(Geist Mono). 굵기 300/400/600/700(`--weight-*`).
- 본문은 한글을 띄어쓰기에서 줄바꿈한다(`word-break: keep-all`, 긴 단어는 `overflow-wrap: anywhere`).
- **글자 크기는 챗봇 창 너비에 비례해 연속으로 커지고 줄어든다**(창은 CSS 컨테이너, `cqi` 단위). `clamp(최소, 최소 + (창 너비 - 360px) x 기울기, 최대)` 형식이고 360px 이하는 최소, 860px 이상은 최대다. 이 범위가 사용자가 창을 끌어 조절할 수 있는 너비 범위(`--chat-min-width`~`--chat-max-width`)와 같아서, 어떤 크기로 바꿔도 글자가 창에 맞게 따라온다.

| 토큰 | 최소 (360px) | 기본 창 (440px) | 최대 (860px) | 쓰임 |
|---|---:|---:|---:|---|
| `--text-xs` | 12px | 12.4px | 14.5px | 캡션, 라벨, 출처·안내 문구 |
| `--text-sm` | 13px | 13.5px | 16px | 칩, 보조 설명 |
| `--text-base` | 14.5px | 15px | 18px | 대화·폼 본문 |
| `--text-md` | 16px | 16.5px | 19px | 입력창(16px 미만 금지: 모바일 확대 방지) |
| `--text-lg` | 19px | 19.8px | 24px | 워드마크 |
| `--text-xl` | 24px | 25.3px | 32px | 큰 제목 |

- 기본 창(440px)의 본문이 약 15px가 되도록 맞췄다. 창 대비 글자 비율은 이전(380px 창에 본문 15.9px, 4.2%)보다 작은 3.4%다. 창이 커진 만큼 글자가 같이 커지지 않도록 범위를 창 기준으로 다시 잡았다.
- 전체 화면 확대 때는 본문 열이 최대 760px이므로 상한(본문 18px)이 그 열에 맞는 크기다.
- 이력: 최초 고정 크기 12.5~25px -> 한때 최소 17px(창에 비해 크다는 의견) -> 현재 최소 14.5px.
- 줄 간격 `--leading-*`(1.3~1.75), 자간 `--tracking-*`.

## 3. 크기, 간격, 모양

- 간격(4px 기준): `--space-0-5`(2) `1`(4) `2`(8) `3`(12) `4`(16) `5`(20) `6`(24) `7`(28) `8`(32) `10`(40)
- 모서리: `--radius-sm` 4, `md` 8, `lg` 12, `xl` 20, `full` 9999, `round` 50%
- 컨트롤 크기는 글자와 함께 커진다(창 너비 360~860px): `--control-sm` 40~44, `md` 42~48, `lg` 46~52. 런처 `--control-xl` 56 고정.
- 아이콘: `--icon-sm` 15~19px(헤더 도구), 선 굵기 `--stroke-thin` 1.25(가느다란 선 아이콘).
- 그림자 `--shadow-float`, `--shadow-card`, `--shadow-panel` / 모션 `--ease`, `--ease-out`, `--duration-fast|base|medium|slow` / 겹침 `--z-handle|launcher|chat|toast`

## 4. 반응형

- 기본 창 크기: `--chat-width` = `clamp(440px, 36vw, 600px)`(화면에 맞춰 연속 변화), 높이 `--chat-height` = `min(clamp(560px, 90dvh, 900px), 화면 - 여백)`.
- **사용자가 직접 크기를 조절한다**(떠 있는 창만). 한계: 너비 `--chat-min-width` 360 ~ `--chat-max-width` 860px(화면 - 여백 이하), 높이 `--chat-min-height` 440px ~ 화면 - 여백.
  - 왼쪽 위 모서리: 가로+세로, 왼쪽 가장자리: 가로, 위쪽 가장자리: 세로. 창이 화면 오른쪽 아래에 붙어 있어서 왼쪽·위쪽을 끌면 커진다.
  - 표시: 모서리의 ㄱ자 표시(항상 보임, 창이 열릴 때 세 번 깜박임), 가장자리에 마우스를 올리면 강조색 띠, 커서 `nwse-resize`/`ew-resize`/`ns-resize`, 툴팁 "끌어서 크기 조절 (두 번 누르면 처음 크기)".
  - 키보드: 모서리 손잡이에 포커스한 뒤 방향키(왼쪽·위쪽이 커짐, 한 번에 `--resize-step` 24px), Enter/Home 또는 두 번 누르기(더블클릭)로 처음 크기.
  - 정한 크기는 이 브라우저의 `localStorage`(`sleeby.chat.size`)에 기억한다(쓸 수 없으면 이번 방문에만 유지). 런타임에 `--chat-width`, `--chat-height`를 px로 덮어쓰는 것이 이 시스템에서 허용되는 유일한 동적 값이다.
- **전체 창 확대**: 헤더의 확대 버튼(⤢)을 누르면 창이 화면을 채우고(`.is-expanded`) 본문 열은 최대 760px로 가운데 정렬된다. 같은 버튼(줄이기 아이콘) 또는 Esc로 원래 크기로 돌아간다. 확대 중에는 크기 조절 핸들을 숨긴다.
- 화면 560px 이하: 챗봇 창이 전체 화면이고, 크기 조절 핸들과 확대 버튼은 숨긴다. `#/chat` 주소: 전체 화면 + 본문 최대 760px.
- 창 너비 640px 이상: 주제 카드를 3열로 배치(`@container chat`).
- 넘침 방지: 컨트롤은 `min-height`, 모든 자식 `min-width: 0`, 본문 `overflow-x: hidden`, 칩 `max-width: 100%`.
- 검증(브라우저 실측, 긴 답변·출처 칩이 있는 상태):
  - 창 너비 360~860px(360, 400, 440, 500, 560, 640, 720, 800, 860): 본문 14.5 -> 15(440) -> 18px(860), 입력창 16 -> 19px, 아이콘 15 -> 19px. 모든 너비에서 가로 넘침·글자 잘림 없음.
  - 기본 창 440x684(1100x760 화면). 전체 창 확대: 1100x760, 본문 열 760px, 본문 18px. Esc로 440x684 복귀. 모바일 375x812: 전체 화면, 본문 14.6px, 크기 핸들·확대 버튼 숨김, 문서 가로 스크롤 없음.

## 5. 컴포넌트

| 컴포넌트 | 클래스 | 규칙 |
|---|---|---|
| 런처 | `.launcher` | 알약, 황동 테두리, 램프 점(`.dot`) |
| 챗봇 창 | `.chat` | `--gradient-panel`, `--radius-xl`, 컨테이너. 확대 시 `.is-expanded` |
| 헤더 도구 | `.tools`, `.tool`, `.tool.is-icon` | 오른쪽 끝 정렬: `[새로고침] [확대/줄이기] [-]`(대화가 있을 때만 새로고침). 아이콘 버튼은 정사각형 + 가느다란 선 아이콘(`.icon`). 닫기는 "-" 아이콘 |
| 봇 말풍선 | `.msg.bot .bot-text` | 아바타 옆 둥근 네모(왼쪽 위만 작은 모서리). **답변, 참고한 자료(`.sources`), 문의 버튼을 한 말풍선 안에 넣고** 참고한 자료는 구분선으로 나눠 어떤 답변의 자료인지 구분한다 |
| 사용자 말풍선 | `.msg.user` | 우측 raised 배경 |
| 첫 인사 | `GREETING` | 대화 맨 위 봇 말풍선 "안녕하세요! 무엇을 도와드릴까요?" (초기화해도 유지) |
| 안내 상자 | `.mode-unknown`, `.mode-partial` | 봇 말풍선의 점선 테두리 + `--fill-lamp-subtle` 변형 |
| 칩/버튼 | `.pill`, `.pill.solid` | 알약, solid는 강조색 |
| 출처 칩 | `.sources .pill` | 점수는 개발 모드(`VITE_SHOW_SCORE`)에서만 |
| 입력창 | `.composer`, `.send` | 알약, 입력 중이면 전송 버튼 강조. 전체 창 확대(`.is-expanded`)에서는 높이 `--control-composer-expanded`(68px)로 키우고 창 맨 아래에 붙인다 |
| 확인 팝업 | `.modal-backdrop`, `.modal` | 창 안쪽 오버레이(`--scrim`, `--z-popup`). 새로고침 아이콘을 누르면 "이전 질문과 답변 기록은 돌아가지 못합니다." + `대화 이어가기`(기본 포커스) / `새 대화`(solid). Esc는 팝업만 닫는다 |
| 문의 폼 | `.inquiry` | 필드 `--color-bg-field` |

## 6. 운영

- 새 값이 필요하면 `tokens.css`에 토큰을 추가한 뒤 쓴다. 화면 CSS에 헥스, rgba, px, 시간, 이징을 직접 쓰면 `npm run lint:design`이 실패한다.
- 예외: `index.html`의 `theme-color`(CSS 변수를 쓸 수 없음)와 `@media` 조건의 px(브레이크포인트 560/720/960).
- 아이콘: 헤더 도구는 `Icon.jsx`의 선 SVG(새로고침, 확대, 줄이기, "-"), 나머지(아바타 ☾, 런처 ●, 전송 ↑)는 아직 글리프 문자다. 레퍼런스의 SVG 아이콘 체계를 모두 적용한 것은 아니다.

## 7. 데모 빌드

- 백엔드 없이 확인하는 미리보기: `VITE_DEMO=true` + `frontend/vite.demo.config.js`(출력 `dist-demo`). `api/demoEngine.js`가 `data/*.json`을 글자 겹침으로 검색해 답한다(실제 RAG가 아님, 일반 빌드에는 포함되지 않음).
