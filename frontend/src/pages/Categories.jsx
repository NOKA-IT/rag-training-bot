import { useState, useEffect } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext.jsx'

export default function Categories() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [categories, setCategories] = useState([])
  const [departments, setDepartments] = useState([])
  const [name, setName] = useState('')
  const [deptId, setDeptId] = useState('')
  const [msg, setMsg] = useState('')

  const load = () => client.get('/categories').then((r) => setCategories(r.data)).catch(() => {})

  useEffect(() => {
    load()
    if (isAdmin) client.get('/departments').then((r) => setDepartments(r.data)).catch(() => {})
  }, [])

  const deptName = (id) => departments.find((d) => d.id === id)?.name || (id ? `#${id}` : 'Global')

  const create = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setMsg('')
    try {
      const body = { name }
      if (isAdmin && deptId) body.department_id = Number(deptId)
      await client.post('/categories', body)
      setName(''); load()
    } catch (err) {
      setMsg('Error: ' + (err.response?.data?.detail || 'failed'))
    }
  }

  const remove = async (id) => {
    if (!confirm('Delete category?')) return
    await client.delete(`/categories/${id}`)
    load()
  }

  return (
    <div className="page">
      <h2>Categories</h2>
      <form className="card" onSubmit={create}>
        <h3>Create Category</h3>
        {msg && <div className="error">{msg}</div>}
        <div className="grid">
          <div>
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          {isAdmin && (
            <div>
              <label>Department (optional → global)</label>
              <select value={deptId} onChange={(e) => setDeptId(e.target.value)}>
                <option value="">Global / company-wide</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          )}
          {!isAdmin && <div className="muted self-end">Created in your department.</div>}
        </div>
        <button className="btn-primary">Create</button>
      </form>

      <div className="card">
        <h3>Existing Categories</h3>
        <table className="table">
          <thead><tr><th>Name</th><th>Department</th><th></th></tr></thead>
          <tbody>
            {categories.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{deptName(c.department_id)}</td>
                <td><button className="btn-danger" onClick={() => remove(c.id)}>Delete</button></td>
              </tr>
            ))}
            {categories.length === 0 && <tr><td colSpan="3" className="muted">No categories yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
