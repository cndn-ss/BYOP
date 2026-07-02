import { useState, useRef, useEffect } from 'react'
import { API } from '../api'

const INITIAL = [{
  role: 'bot',
  text: "Hi! I'm the GeoSentinel+ AI. Ask me about landslide risk, the Garhwal Himalaya geology, the MCT zone, or how the model works.",
}]

export default function Chatbot({ onClose }) {
  const [messages, setMessages] = useState(INITIAL)
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setLoading(true)
    try {
      const res  = await fetch(API.chat, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'bot',
        text: res.ok ? data.response : (data.detail || 'Something went wrong.'),
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: 'Network error. Is the backend running?',
      }])
    }
    setLoading(false)
  }

  return (
    /* ── centered, 32px above bottom, rectangular, slides up ── */
    <div
      className="chatbot-slide-up"
      style={{
        position: 'fixed',
        bottom: 32,
        left: '50%',
        transform: 'translateX(-50%)',
        width: 560,
        height: 340,
        zIndex: 2000,
        borderRadius: 4,           /* nearly square corners — rectangular look */
        background: 'rgba(255,255,255,0.94)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(0,0,0,0.10)',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 16px',
          borderBottom: '1px solid rgba(0,0,0,0.07)',
          background: 'rgba(240,253,244,0.95)',
          borderRadius: '4px 4px 0 0',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: '#22c55e', display: 'inline-block',
          }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>
            GeoSentinel+ AI
          </span>
        </div>
        <button
          onClick={onClose}
          style={{ fontSize: 18, color: '#9ca3af', background: 'none', border: 'none', cursor: 'pointer', lineHeight: 1 }}
          onMouseOver={e => e.target.style.color = '#111'}
          onMouseOut={e => e.target.style.color = '#9ca3af'}
        >×</button>
      </div>

      {/* Messages area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              background: m.role === 'user' ? '#22c55e' : '#f3f4f6',
              color: m.role === 'user' ? '#fff' : '#374151',
              padding: '7px 12px',
              borderRadius: 8,
              fontSize: 12,
              lineHeight: 1.6,
            }}
          >
            {m.text}
          </div>
        ))}
        {loading && (
          <div style={{
            alignSelf: 'flex-start', background: '#f3f4f6',
            color: '#9ca3af', padding: '7px 12px',
            borderRadius: 8, fontSize: 12,
          }}>
            Thinking…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div style={{
        padding: '10px 12px',
        borderTop: '1px solid rgba(0,0,0,0.07)',
        display: 'flex', gap: 8, flexShrink: 0,
        background: 'rgba(255,255,255,0.8)',
        borderRadius: '0 0 4px 4px',
      }}>
        <input
          style={{
            flex: 1,
            background: '#f9fafb',
            border: '1px solid #e5e7eb',
            borderRadius: 6,
            padding: '7px 12px',
            fontSize: 12,
            color: '#111827',
            outline: 'none',
          }}
          placeholder="Ask about landslide risk, geology, or the model…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          onFocus={e => e.target.style.borderColor = '#22c55e'}
          onBlur={e => e.target.style.borderColor = '#e5e7eb'}
        />
        <button
          onClick={send}
          disabled={loading}
          style={{
            background: loading ? '#86efac' : '#22c55e',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            padding: '7px 18px',
            fontSize: 12,
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'background 0.15s',
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
