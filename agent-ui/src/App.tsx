import { useEffect, useRef, useState, type FormEvent } from 'react'
import { sendMessage, type Intent } from './api'
import './App.css'

interface ChatMessage {
  role: 'user' | 'agent' | 'error'
  text: string
  intent?: Intent
}

const INTENT_LABELS: Record<Intent, string> = {
  inv_mgmt_agent: 'Inventory',
  item_transfer_agent: 'Transfer',
  vendor_agent: 'Vendor',
}

export default function App() {
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID())
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const activeSession = useRef(sessionId)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function newSession() {
    const id = crypto.randomUUID()
    activeSession.current = id
    setSessionId(id)
    setMessages([])
    setInput('')
    setLoading(false)
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    const session = sessionId
    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)
    try {
      const res = await sendMessage(session, text)
      if (activeSession.current !== session) return
      setMessages((prev) => [...prev, { role: 'agent', text: res.message, intent: res.intent }])
    } catch (err) {
      if (activeSession.current !== session) return
      const detail = err instanceof Error ? err.message : 'Something went wrong'
      setMessages((prev) => [...prev, { role: 'error', text: detail }])
    } finally {
      if (activeSession.current === session) setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Inventory Agent</h1>
          <span className="session-id">Session {sessionId.slice(0, 8)}</span>
        </div>
        <button type="button" onClick={newSession}>
          New session
        </button>
      </header>

      <main className="messages">
        {messages.length === 0 && (
          <p className="empty">
            Ask about inventory, move items between warehouses, or raise a purchase order.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.intent && <span className="intent">{INTENT_LABELS[m.intent]}</span>}
            <p>{m.text}</p>
          </div>
        ))}
        {loading && <div className="message agent typing">Thinking…</div>}
        <div ref={bottomRef} />
      </main>

      <form className="composer" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
