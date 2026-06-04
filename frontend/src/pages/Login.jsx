import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) { navigate('/chat'); return null }

  const submit = async (e) => {
    e.preventDefault()
    setError(''); setBusy(true)
    try {
      await login(username, password)
      navigate('/chat')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <h1>🤖 RAG Training Bot</h1>
        <p className="muted">Sign in with the credentials provided by your admin.</p>
        {error && <div className="error">{error}</div>}
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="btn-primary" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
