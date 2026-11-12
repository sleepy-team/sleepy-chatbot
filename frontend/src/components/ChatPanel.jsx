import { useEffect, useRef, useState } from 'react';
import { useChat } from '../hooks/useChat';
import MessageBubble from './MessageBubble';

const TOPICS = [
  {
    name: '제품 소개',
    hint: '무엇인지, 어떤 원리인지',
    questions: [
      '구성품에는 어떤 것들이 들어 있나요?',
      '슬리비는 어떤 원리로 수면과 이완을 돕도록 설계되었나요?',
    ],
  },
  {
    name: '사용 방법·유의사항',
    hint: '착용, 충전, 주의할 점',
    questions: [
      '슬리비를 사용하려면 스마트폰이나 전용 앱이 필요한가요?',
      '여행할 때 비행기나 기차 안에서 사용해도 되나요?',
      '슬리비가 충전되지 않을 때는 어떻게 하나요?',
    ],
  },
  {
    name: '구매·문의',
    hint: '배송, 교환, 환불, 상담',
    questions: [
      '제품을 주문하면 배송까지 얼마나 걸리나요?',
      '제품이 귀에 맞지 않으면 교환하거나 환불받을 수 있나요?',
      '상담원 또는 1:1 문의는 어디에서 신청할 수 있나요?',
    ],
  },
];

export default function ChatPanel({ isSolo = false, onClose }) {
  const { messages, isLoading, sessionId, ask, stop, reset } = useChat();
  const [input, setInput] = useState('');
  const [topic, setTopic] = useState(null);
  const [isConfirmingReset, setIsConfirmingReset] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const submit = (event) => {
    event.preventDefault();
    ask(input);
    setInput('');
  };

  const confirmReset = () => {
    reset();
    setTopic(null);
    setIsConfirmingReset(false);
  };

  const isTalking = messages.length > 0;

  return (
    <section className={`chat ${isSolo ? 'is-solo' : ''}`} aria-label="슬리비 안내 도우미">
      <header className="chat-head">
        <div className="chat-name">
          <b>SLEEBY</b>
          <span>안내 도우미</span>
        </div>
        <div className="tools">
          {isTalking && (
            <button type="button" className="tool" onClick={() => setIsConfirmingReset(true)}>
              초기화
            </button>
          )}
          <button type="button" className="tool" onClick={onClose}>
            {isSolo ? '나가기' : '닫기'}
          </button>
        </div>
      </header>

      <div className="chat-body">
        {isConfirmingReset && (
          <div className="confirm" role="alertdialog">
            <span>대화를 모두 지울까요?</span>
            <div className="chips">
              <button type="button" className="pill solid" onClick={confirmReset}>
                지우기
              </button>
              <button type="button" className="pill" onClick={() => setIsConfirmingReset(false)}>
                취소
              </button>
            </div>
          </div>
        )}
        {!isTalking && (
          <div className="welcome">
            <div className="moon" aria-hidden="true">
              ☾
            </div>
            <h2>편안한 밤을 위한 안내를 도와드릴게요</h2>
            <p>제품 자료와 FAQ를 근거로 답해요. 수면 효과나 의학적 판단은 안내하지 않아요.</p>
            <div className="topics">
              {TOPICS.map((item) => (
                <button
                  key={item.name}
                  type="button"
                  className={`topic ${topic?.name === item.name ? 'is-on' : ''}`}
                  onClick={() => setTopic(item)}
                >
                  <span>
                    <small>{item.hint}</small>
                    <strong>{item.name}</strong>
                  </span>
                  <span aria-hidden="true">→</span>
                </button>
              ))}
            </div>
            {topic && (
              <div className="chips questions">
                {topic.questions.map((question) => (
                  <button
                    key={question}
                    type="button"
                    className="pill"
                    onClick={() => ask(question)}
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        <div className="msgs">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} sessionId={sessionId} />
          ))}
          {isLoading && (
            <div className="msg bot">
              <span className="av" aria-hidden="true">
                ☾
              </span>
              <span className="typing" aria-label="답변을 찾는 중">
                <i />
                <i />
                <i />
              </span>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </div>

      <footer className="chat-foot">
        <form className={`composer ${input.trim() ? 'has-text' : ''}`} onSubmit={submit}>
          <input
            id="chat-input"
            aria-label="질문 입력"
            placeholder="궁금한 점을 입력해 주세요"
            value={input}
            onChange={(event) => setInput(event.target.value)}
          />
          {isLoading ? (
            <button type="button" className="send" aria-label="답변 멈추기" onClick={stop}>
              ■
            </button>
          ) : (
            <button type="submit" className="send" aria-label="보내기" disabled={!input.trim()}>
              ↑
            </button>
          )}
        </form>
        <p className="chat-note">AI 답변은 자료에 없는 내용을 확인하지 못할 수 있어요.</p>
      </footer>
    </section>
  );
}
