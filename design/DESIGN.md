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
- **글자 크기는 챗봇 창 너비에 비례해 연속으로 커지고 줄어든다**(창은 CSS 컨테이너, `cqi` 단위). `clamp(최소, 최소 + (창 너비 - 360px) x 기울기, 최대)` 형식이고 360px 이하는 최소, 520px 이상은 최대다.

| 토큰 | 최소 (360px) | 최대 (520px) | 쓰임 |
|---|---:|---:|---|
| `--text-xs` | 14px | 16px | 캡션, 라벨, 출처 안내 |
| `--text-sm` | 15px | 17.5px | 칩, 보조 설명 |
| `--text-base` | 17px | 20px | 대화·폼 본문 |
| `--text-md` | 18px | 21.5px | 입력창, 강조 |
| `--text-lg` | 20px | 24px | 워드마크 |
| `--text-xl` | 28px | 36px | 환영 제목 |

이전 고정 크기는 12.5~25px였다. 줄 간격 `--leading-*`(1.3~1.75), 자간 `--tracking-*`.

## 3. 크기, 간격, 모양

- 간격(4px 기준): `--space-0-5`(2) `1`(4) `2`(8) `3`(12) `4`(16) `5`(20) `6`(24) `7`(28) `8`(32) `10`(40)
- 모서리: `--radius-sm` 4, `md` 8, `lg` 12, `xl` 20, `full` 9999, `round` 50%
- 컨트롤 높이는 글자와 함께 커진다: `--control-sm` 40~46, `md` 44~52, `lg` 48~56(모두 터치 목표 44px 이상). 런처 `--control-xl` 56 고정.
- 그림자 `--shadow-float`, `--shadow-card`, `--shadow-panel` / 모션 `--ease`, `--ease-out`, `--duration-fast|base|medium|slow` / 겹침 `--z-launcher|chat|toast`

## 4. 반응형

- 챗봇 창 너비: `--chat-width` = `clamp(380px, 32vw, 520px)`(화면에 맞춰 연속 변화), 높이 `min(clamp(520px, 86dvh, 840px), 화면 - 여백)`.
- 화면 560px 이하: 챗봇 창이 전체 화면. `#/chat` 주소: 전체 화면 + 본문 최대 760px.
- 창 너비 640px 이상: 주제 카드를 3열로 배치(`@container chat`).
- 넘침 방지: 컨트롤은 `min-height`, 모든 자식 `min-width: 0`, 본문 `overflow-x: hidden`, 칩 `max-width: 100%`.
- 검증(브라우저 실측, 긴 답변·출처 칩·문의 폼이 열린 상태):
  - 창 너비 320~760px: 본문 17px(360px 이하) -> 17.3(380) -> 18.5(440) -> 20px(520px 이상). 가로 넘침·글자 잘림 없음.
  - 화면 크기별 창: 375x812 전체 화면(본문 17.3px), 560x800 전체 화면(20px), 561~800 너비 380px 창(17.3px), 1440x900 461x774(18.9px), 1920x1080 520x840(20px). 문서 가로 스크롤 없음.

## 5. 컴포넌트

| 컴포넌트 | 클래스 | 규칙 |
|---|---|---|
| 런처 | `.launcher` | 알약, 황동 테두리, 램프 점(`.dot`) |
| 챗봇 창 | `.chat` | `--gradient-panel`, `--radius-xl`, 컨테이너 |
| 말풍선 | `.msg.user`, `.msg.bot` | 사용자는 우측 raised 배경, 봇은 아바타 + 글 |
| 안내 상자 | `.mode-unknown`, `.mode-partial` | 점선 테두리 + `--fill-lamp-subtle` |
| 칩/버튼 | `.pill`, `.pill.solid` | 알약, solid는 강조색 |
| 출처 칩 | `.sources .pill` | 점수는 개발 모드(`VITE_SHOW_SCORE`)에서만 |
| 입력창 | `.composer`, `.send` | 알약, 입력 중이면 전송 버튼 강조 |
| 문의 폼 | `.inquiry` | 필드 `--color-bg-field` |

## 6. 운영

- 새 값이 필요하면 `tokens.css`에 토큰을 추가한 뒤 쓴다. 화면 CSS에 헥스, rgba, px, 시간, 이징을 직접 쓰면 `npm run lint:design`이 실패한다.
- 예외: `index.html`의 `theme-color`(CSS 변수를 쓸 수 없음)와 `@media` 조건의 px(브레이크포인트 560/720/960).
- 아이콘은 아직 글리프 문자(●, ☾, ↑)다. 레퍼런스의 SVG 아이콘 체계는 적용하지 않았다.
