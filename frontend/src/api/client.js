const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`요청에 실패했어요 (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

export function sendChat(message, sessionId, signal) {
  return request('/api/chats', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });
}

export function resetChat(sessionId) {
  return request(`/api/chats/${sessionId}`, { method: 'DELETE' });
}

export function sendInquiry(payload) {
  return request('/api/inquiries', { method: 'POST', body: JSON.stringify(payload) });
}
