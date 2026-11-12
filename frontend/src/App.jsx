import { useEffect, useState } from 'react';
import ChatPanel from './components/ChatPanel';

const isSoloHash = () => window.location.hash === '#/chat';

export default function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [isSolo, setIsSolo] = useState(isSoloHash());

  useEffect(() => {
    const onHashChange = () => setIsSolo(isSoloHash());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  if (isSolo) {
    return <ChatPanel isSolo onClose={() => (window.location.hash = '#/')} />;
  }

  return (
    <main className="stage">
      <p className="wordmark">SLEEBY</p>
      <p className="stage-note">
        오른쪽 아래 버튼으로 안내 도우미를 열어 보세요.
        <br />
        전체 화면은 주소 끝에 <code>#/chat</code>을 붙이면 열려요.
      </p>
      <button type="button" className="launcher" hidden={isOpen} onClick={() => setIsOpen(true)}>
        <span className="dot">●</span>안내 도우미
      </button>
      {isOpen && <ChatPanel onClose={() => setIsOpen(false)} />}
    </main>
  );
}
