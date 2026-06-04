import { useState, useEffect, useRef } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext.jsx'

export default function Chat() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [departments, setDepartments] = useState([])
  const [deptFilter, setDeptFilter] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    client.get('/departments').then((r) => setDepartments(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (e) => {
    e.preventDefault()
    const q = input.trim()
    if (!q || busy) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    setBusy(true)
    try {
      const res = await client.post('/chat', {
        question: q,
        department_id: deptFilter ? Number(deptFilter) : null,
      })
      setMessages((m) => [...m, {
        role: 'bot',
        text: res.data.answer,
        sources: res.data.sources,
      }])
    } catch (err) {
      setMessages((m) => [...m, {
        role: 'bot',
        text: 'Error: ' + (err.response?.data?.detail || 'request failed'),
      }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <h2>Ask the Training Bot</h2>
        {(user?.role === 'admin') && (
          <select value={deptFilter} onChange={(e) => setDeptFilter(e.target.value)}>
            <option value="">All accessible documents</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        )}
      </div>

      <div className="chat-window">
        {messages.length === 0 && (
          <div className="empty muted">
            Ask a question about your company documents to get started.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <div className="bubble-text">{m.text}</div>
            {m.sources && m.sources.length > 0 && (
              <div className="sources">
                <strong>Sources:</strong>
                <ul>
                  {m.sources.map((s, j) => (
                    <li key={j}>{s.filename}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        {busy && <div className="bubble bot"><em>Thinking…</em></div>}
        <div ref={endRef} />
      </div>

      <form className="chat-input" onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question…"
        />
        <button className="btn-primary" disabled={busy}>Send</button>
      </form>
    </div>
  )
}
