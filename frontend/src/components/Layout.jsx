import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const isStaff = user && (user.role === 'admin' || user.role === 'uploader')

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">🤖 RAG Training Bot</div>
        <nav className="nav">
          <NavLink to="/chat">Chat</NavLink>
          {isStaff && <NavLink to="/documents">Documents</NavLink>}
          {isStaff && <NavLink to="/categories">Categories</NavLink>}
          {user?.role === 'admin' && <NavLink to="/admin">Admin</NavLink>}
        </nav>
        <div className="user-box">
          <span className="role-badge">{user?.role}</span>
          <span>{user?.username}</span>
          <button className="btn-secondary" onClick={handleLogout}>Logout</button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
