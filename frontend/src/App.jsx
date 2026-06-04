import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Chat from './pages/Chat.jsx'
import Documents from './pages/Documents.jsx'
import Categories from './pages/Categories.jsx'
import Admin from './pages/Admin.jsx'

function Protected({ children, roles }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="center">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/chat" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route path="/chat" element={<Chat />} />
        <Route
          path="/documents"
          element={<Protected roles={['admin', 'uploader']}><Documents /></Protected>}
        />
        <Route
          path="/categories"
          element={<Protected roles={['admin', 'uploader']}><Categories /></Protected>}
        />
        <Route
          path="/admin"
          element={<Protected roles={['admin']}><Admin /></Protected>}
        />
      </Route>
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  )
}
