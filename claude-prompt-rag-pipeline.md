<context>
슬리비(Sleeby) 고객상담 챗봇의 RAG 모듈(`backend/rag/`)을 처음부터 만든다.
지금은 AGENTS.md의 "개인별 RAG 구성" 단계다. 팀원 4명이 각자 RAG를 만든 뒤 같은 평가 세트로 비교해 하나를 채택한다.
그래서 이번 구현은 (1) FastAPI 없이 단독 실행·평가가 가능해야 하고, (2) 실험 설정을 바꿔 가며 비교할 수 있어야 하며, (3) 다른 팀원 구현과 공정하게 비교되도록 공통 데이터를 그대로 써야 한다.

AGENTS.md, CONVENTION.md는 CLAUDE.md로 이미 불러와져 있다. 아래 지시와 충돌하면 AGENTS.md를 우선하고, 충돌 사실을 나에게 알려라.
</context>

<before_coding>
코드를 쓰기 전에 아래를 먼저 하고, 결과와 구현 계획을 보여 준 뒤 내 승인을 기다려라.

1. `docs/data-sources.md`를 읽는다.
2. `data/` 폴더를 확인한다.
   - `data/faq.json`이 없으면 멈추고 나에게 요청한다. PDF·docx·`docs/Sleeby_FAQ.md`에서 직접 만들지 않는다 (팀 공통 파일이어야 비교가 공정하다).
   - 있으면 실제 필드 구조(질문/답변/카테고리/번호/status/company_provided/support_required 등)를 확인하고 요약해 보여 준다. 필드 이름을 추측해서 코드를 쓰지 않는다.
   - 제품 정보 JSON이 있는지도 확인한다.
3. `backend/pyproject.toml` 존재 여부와 설치된 패키지 버전(langchain, langchain-openai, langchain-qdrant, qdrant-client, rank-bm25)을 확인한다. 없으면 필요한 의존성 목록을 제안하고 `uv add` 전에 확인받는다.
4. 사용할 LangChain API(특히 `EnsembleRetriever`, `BM25Retriever`, Qdrant 연동)가 설치된 버전에서 어느 패키지 경로에 있고 비동기를 어떻게 지원하는지 확인한다. 기억에 의존하지 말고 설치된 소스를 직접 확인한다.
</before_coding>

<requirements>
<data>
- 인덱싱 대상은 `data/`의 JSON뿐이다. `docs/` 원본(PDF, md, docx)은 읽지 않는다. `3.IR 자료.pdf` 내용은 어떤 경우에도 넣지 않는다.
- 답변이 비어 있거나 `status: pending`인 항목은 인덱싱하지 않는다.
- 로더는 파일 개수·항목 개수·특정 문구에 의존하지 않는다 (FAQ는 계속 갱신된다). `data/` 안의 JSON을 순회하되, 문서 유형(FAQ / 제품 정보)은 파일 내용이나 필드로 판별한다.
- 모든 Document 메타데이터에 출처 표기에 필요한 값(유형, FAQ 번호 또는 문서명, 카테고리)과 원본 플래그(`company_provided`, `support_required` 등 실제로 있는 것)를 넣는다.
</data>

<chunking>
- FAQ: 질문+답변 1세트 = Document 1개. 쪼개지 않는다.
- 제품 정보 등 긴 텍스트: `RecursiveCharacterTextSplitter`. chunk_size·chunk_overlap 기본값은 400/50으로 하되 설정 파일에서 읽는다.
</chunking>

<vectorstore>
- Qdrant, 임베딩은 OpenAI `text-embedding-3-small`.
- `AsyncQdrantClient`로 컬렉션 생성·업서트·검색을 비동기로 한다. Qdrant 실행 방식(`:memory:` / 로컬 path / 서버 URL)은 설정 파일로 고른다. 기본값은 별도 설치가 필요 없는 로컬 모드로 둔다.
- LangChain의 Qdrant 래퍼가 비동기 클라이언트를 제대로 지원하지 않으면, `AsyncQdrantClient`를 직접 쓰는 얇은 커스텀 retriever(`_aget_relevant_documents` 구현)로 대체한다. 어느 쪽을 택했는지와 이유를 보고한다.
</vectorstore>

<retrieval>
- 하이브리드: BM25(가중치 0.4) + 벡터 검색(가중치 0.6)을 `EnsembleRetriever`로 결합, 최종 top-k=3. 가중치와 k는 설정 파일에서 읽는다.
- 검색 방식은 AGENTS.md상 "검토 중"이므로 설정 값 하나로 `vector` / `bm25` / `hybrid`를 바꿀 수 있게 한다. 이 이상의 추상화는 하지 않는다.
- BM25 기본 토크나이저는 공백 기준이라 한국어 조사 때문에 매칭이 약하다. 개선이 필요하다고 판단되면 방법(예: 형태소 분석기 도입)을 제안만 하고, 새 의존성은 내 승인 후에 추가한다.
</retrieval>

<prompt>
- 시스템 프롬프트는 코드에 하드코딩하지 않고 `backend/rag/prompts/` 아래 텍스트 파일(예: `system.md`)로 두고, `prompts.py`(또는 loader 함수)가 읽어 `ChatPromptTemplate`을 만든다.
- 시스템 프롬프트에 담을 규칙:
  - 제공된 context에 있는 내용만 근거로 답한다.
  - context에 답이 없거나 불확실하면 추측하지 말고 슬리피 고객센터 1:1 문의를 안내한다.
  - 슬리비와 관련 없는 질문에는 답변 가능한 범위(제품 특징, 사용 방법, 유의사항, 구매)를 안내한다.
  - 슬리비는 질환을 진단·치료하는 제품이 아니다. 수면·건강 효과를 단정하지 않는다.
  - `support_required` 항목이 근거면 상담원 연결을 함께 안내한다.
  - 근거를 사용한 답변 끝에 `[출처: FAQ Q3]` 또는 `[출처: 제품소개서]` 형식으로 출처를 붙인다. 문의 안내만 하는 경우에는 붙이지 않는다.
  - 말투는 FAQ 원문처럼 친근한 존댓말("~해요")을 쓴다.
- context 문자열에는 각 문서 앞에 출처 라벨을 붙여서, 모델이 출처를 지어내지 않고 라벨을 그대로 옮기게 한다.
</prompt>

<chain>
- LCEL로 `prompt | llm | StrOutputParser()` 체인을 구성한다. LLM은 OpenAI `gpt-4o-mini`, temperature 등은 설정 파일에서 읽는다.
- 메인 함수: `async def generate_rag_response(query: str) -> RAGResponse`
  - retriever를 `ainvoke`로 비동기 검색 → `context`, `question`을 체인에 전달 → 체인도 `ainvoke`.
  - 반환값은 답변 문자열과 참조 Document 리스트를 담은 타입(dataclass 또는 Pydantic 모델)으로 정의한다. tuple로 반환하지 않는다.
- 인덱싱(임베딩·업서트)은 질문마다 반복하지 않는다. 인덱스 구축 함수와 질의 함수를 분리한다.
</chain>

<config>
- 모든 실험 값(모델명, 임베딩 모델, chunk 설정, 검색 방식, 가중치, k, Qdrant 위치, 프롬프트 파일 경로)은 `configs/rag/` 아래 새 YAML 파일(예: `configs/rag/hybrid-v1.yaml`)에 둔다. 기존 설정 파일은 덮어쓰지 않는다.
- API 키는 저장소 루트 `.env`에서 `pydantic-settings`로 읽는다. `.env.example`이 없으면 만든다(값은 비워 둔다).
</config>
</requirements>

<file_layout>
아래 구성을 기본으로 하되, 더 나은 분리가 있으면 계획 단계에서 제안해라.

```
backend/rag/
├── __init__.py
├── config.py        # 설정 파일 + .env 로드
├── loaders.py       # data/ JSON → Document
├── splitters.py     # FAQ는 그대로, 긴 텍스트만 분할
├── vectorstore.py   # AsyncQdrantClient 컬렉션 생성·인덱싱
├── retrievers.py    # vector / bm25 / hybrid
├── prompts.py       # prompts/ 파일 읽어 템플릿 생성
├── prompts/system.md
├── chain.py         # LCEL 체인, generate_rag_response
└── __main__.py      # CLI: 인덱스 구축 후 질문 1개 실행
configs/rag/hybrid-v1.yaml
```
</file_layout>

<code_style>
- CONVENTION.md를 따른다: 모든 함수에 타입 힌트, I/O 함수는 `async def`, `async def` 안에서는 비동기 API만 사용(동기 라이브러리는 `def`로 두거나 `asyncio.to_thread`), `print` 대신 `logging`, 주석은 "왜"만.
- RAG 모듈은 FastAPI를 import하지 않는다. FastAPI 서버, 프론트엔드, 평가 스크립트는 이번 작업에 포함하지 않는다.
</code_style>

<verification>
구현 후 아래를 직접 실행하고 결과를 보고해라. 명령은 `&&`로 묶지 말고 하나씩 실행한다 (Windows PowerShell 5.1 호환).

1. `backend/`에서 `uv run ruff check .` 와 `uv run ruff format --check .`
2. `.env`에 OpenAI 키가 있으면 CLI로 아래 4개 질문을 실행해 답변·출처·검색된 문서를 보여 준다. 키가 없으면 실행하지 말고 알려라.
   - FAQ에 있는 질문 1개 (예: "앱 설치가 필요한가요?")
   - 표현을 바꾼 FAQ 질문 1개
   - 자료에 없는 질문 1개 → 문의 안내가 나와야 함
   - 관련 없는 질문 1개 (예: "오늘 날씨 어때?") → 범위 안내가 나와야 함
3. 기대와 다른 결과는 숨기지 말고 원인 추정과 함께 보고한다. 이 단계에서 결과에 맞춰 설정을 튜닝하지는 않는다.
</verification>

<finish>
- 마지막에 변경 파일 목록, 내가 승인한 결정/임의로 정한 결정, 남은 TODO를 정리한다.
- AGENTS.md 절차대로 커밋 메시지 초안을 제안만 한다. 승인 없이 커밋하지 않고, push하지 않는다.
</finish>
