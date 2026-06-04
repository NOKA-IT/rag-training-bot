import { useState, useEffect } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext.jsx'

export default function Documents() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [docs, setDocs] = useState([])
  const [departments, setDepartments] = useState([])
  const [categories, setCategories] = useState([])
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [visibility, setVisibility] = useState('department')
  const [deptId, setDeptId] = useState('')
  const [selectedCats, setSelectedCats] = useState([])
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  const loadDocs = () => client.get('/documents').then((r) => setDocs(r.data)).catch(() => {})
  const loadCats = () => client.get('/categories').then((r) => setCategories(r.data)).catch(() => {})

  useEffect(() => {
    loadDocs(); loadCats()
    client.get('/departments').then((r) => setDepartments(r.data)).catch(() => {})
  }, [])

  const toggleCat = (id) => {
    setSelectedCats((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id])
  }

  const upload = async (e) => {
    e.preventDefault()
    if (!file) { setMsg('Please choose a file.'); return }
    setBusy(true); setMsg('')
    const fd = new FormData()
    fd.append('file', file)
    fd.append('title', title)
    fd.append('visibility', visibility)
    if (isAdmin && visibility === 'department' && deptId) fd.append('department_id', deptId)
    if (selectedCats.length) fd.append('category_ids', selectedCats.join(','))
    try {
      await client.post('/documents', fd)
      setMsg('Uploaded! Processing in background…')
      setFile(null); setTitle(''); setSelectedCats([])
      document.getElementById('file-input').value = ''
      setTimeout(loadDocs, 1500)
    } catch (err) {
      setMsg('Error: ' + (err.response?.data?.detail || 'upload failed'))
    } finally {
      setBusy(false)
    }
  }

  const remove = async (id) => {
    if (!confirm('Delete this document?')) return
    await client.delete(`/documents/${id}`)
    loadDocs()
  }

  return (
    <div className="page">
      <h2>Documents</h2>

      <form className="card" onSubmit={upload}>
        <h3>Upload Document</h3>
        {msg && <div className="info">{msg}</div>}
        <div className="grid">
          <div>
            <label>File (PDF, Word, TXT)</label>
            <input id="file-input" type="file" accept=".pdf,.docx,.doc,.txt,.md"
                   onChange={(e) => setFile(e.target.files[0])} />
          </div>
          <div>
            <label>Title (optional)</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <label>Visibility</label>
            <select value={visibility} onChange={(e) => setVisibility(e.target.value)}>
              <option value="department">Department only</option>
              <option value="general">General company (all users)</option>
            </select>
          </div>
          {isAdmin && visibility === 'department' && (
            <div>
              <label>Department</label>
              <select value={deptId} onChange={(e) => setDeptId(e.target.value)}>
                <option value="">Select department</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          )}
        </div>
        <div className="cats">
          <label>Categories</label>
          <div className="chips">
            {categories.length === 0 && <span className="muted">No categories yet.</span>}
            {categories.map((c) => (
              <label key={c.id} className={`chip ${selectedCats.includes(c.id) ? 'on' : ''}`}>
                <input type="checkbox" checked={selectedCats.includes(c.id)}
                       onChange={() => toggleCat(c.id)} />
                {c.name}
              </label>
            ))}
          </div>
        </div>
        <button className="btn-primary" disabled={busy}>
          {busy ? 'Uploading…' : 'Upload'}
        </button>
      </form>

      <div className="card">
        <h3>Existing Documents</h3>
        <table className="table">
          <thead>
            <tr><th>Title</th><th>File</th><th>Visibility</th><th>Status</th><th>Chunks</th><th></th></tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.title}</td>
                <td>{d.filename}</td>
                <td>{d.visibility === 'general' ? 'General' : 'Department'}</td>
                <td><span className={`status ${d.status}`}>{d.status}</span>
                    {d.error && <div className="muted small">{d.error}</div>}</td>
                <td>{d.chunk_count}</td>
                <td><button className="btn-danger" onClick={() => remove(d.id)}>Delete</button></td>
              </tr>
            ))}
            {docs.length === 0 && <tr><td colSpan="6" className="muted">No documents yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
