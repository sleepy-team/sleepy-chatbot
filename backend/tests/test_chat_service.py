import pytest

from app.services.chat_service import classify_answer


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("아니요. [출처: FAQ Q3]", ("answer", False)),
        ("충전이 안 되면 고객센터로 문의해 주세요. [출처: FAQ Q27]", ("partial", True)),
        ("확인할 수 없어요. 슬리피 고객센터 1:1 문의를 이용해 주세요.", ("unknown", True)),
        ("슬리비와 관련 없는 질문에는 답변할 수 없어요.", ("offtopic", False)),
    ],
)
def test_classify_answer(answer: str, expected: tuple[str, bool]) -> None:
    assert classify_answer(answer) == expected
