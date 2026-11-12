"""prompts/ 의 텍스트 파일을 읽어 프롬프트와 context 문자열을 만든다."""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def load_prompt(prompt_path: Path) -> ChatPromptTemplate:
    system_text = prompt_path.read_text(encoding="utf-8")
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_text),
            # 이전 대화가 없으면 비어 있어서 기존 프롬프트와 같은 입력이 된다
            MessagesPlaceholder("history", optional=True),
            ("human", "{question}"),
        ]
    )


def format_history(history: list[tuple[str, str]] | None) -> list[BaseMessage]:
    """(질문, 답변) 목록을 대화 메시지로 바꾼다."""
    messages: list[BaseMessage] = []
    for question, answer in history or []:
        messages.append(HumanMessage(content=question))
        messages.append(AIMessage(content=answer))
    return messages


def format_context(documents: list[Document]) -> str:
    """문서마다 출처 라벨을 붙여, 모델이 라벨을 그대로 옮기게 한다."""
    if not documents:
        return "(검색된 자료 없음)"
    blocks: list[str] = []
    for doc in documents:
        label = doc.metadata.get("source_label", "출처 미상")
        lines = [f"[출처: {label}]"]
        if doc.metadata.get("support_required"):
            lines.append("(상담원 연결 필요)")
        lines.append(doc.page_content)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
