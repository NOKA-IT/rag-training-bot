import { useState, useEffect } from 'react'
import client from '../api/client'

export default function Admin() {
  const [users, setUsers] = useState([])
  const [departments, setDepartments] = useState([])

  // new user form
  const [u, setU] = useState({ username: '', password: '', email: '', role: 'user', department_id: '' })
  const [userMsg, setUserMsg] = useState('')

  // new department form
  const [deptName, setDeptName] = useState('')
  const [deptDesc, setDeptDesc] = useState('')
  const [deptMsg, setDeptMsg] = useState('')

  const loadUsers = () => client.get('/users').then((r) => setUsers(r.data)).catch(() => {})
  const loadDepts = () => client.get('/departments').then((r) => setDepartments(r.data)).catch(() => {})

  useEffect(() => { loadUsers(); loadDepts() }, [])

  const deptName2 = (id) => departments.find((d) => d.id === id)?.name || '—'

  const createUser = async (e) => {
    e.preventDefault(); setUserMsg('')
    try {
      const body = { ...u }
      body.department_id = u.department_id ? Number(u.department_id) : null
      await client.post('/users', body)
      setU({ username: '', password: '', email: '', role: 'user', department_id: '' })
      loadUsers()
    } catch (err) {
      setUserMsg('Error: ' + (err.response?.data?.detail || 'failed'))
    }
  }

  const deleteUser = async (id) => {
    if (!confirm('Delete user?')) return
    await client.delete(`/users/${id}`); loadUsers()
  }

  const createDept = async (e) => {
    e.preventDefault(); setDeptMsg('')
    try {
      await client.post('/departments', { name: deptName, description: deptDesc })
      setDeptName(''); setDeptDesc(''); loadDepts()
    } catch (err) {
      setDeptMsg('Error: ' + (err.response?.data?.detail || 'failed'))
    }
  }

  const deleteDept = async (id) => {
    if (!confirm('Delete department?')) return
    await client.delete(`/departments/${id}`); loadDepts()
  }

  return (
    <div className="page">
      <h2>Admin Dashboard</h2>

      <div className="card">
        <h3>Create Department</h3>
        {deptMsg && <div className="error">{deptMsg}</div>}
        <form className="row" onSubmit={createDept}>
          <input placeholder="Department name" value={deptName}
                 onChange={(e) => setDeptName(e.target.value)} />
          <input placeholder="Description" value={deptDesc}
                 onChange={(e) => setDeptDesc(e.target.value)} />
          <button className="btn-primary">Add</button>
        </form>
        <table className="table">
          <thead><tr><th>Name</th><th>Description</th><th></th></tr></thead>
          <tbody>
            {departments.map((d) => (
              <tr key={d.id}>
                <td>{d.name}</td><td>{d.description}</td>
                <td><button className="btn-danger" onClick={() => deleteDept(d.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Create User</h3>
        {userMsg && <div className="error">{userMsg}</div>}
        <form className="grid" onSubmit={createUser}>
          <div>
            <label>Username</label>
            <input value={u.username} onChange={(e) => setU({ ...u, username: e.target.value })} />
          </div>
          <div>
            <label>Password</label>
            <input type="text" value={u.password} onChange={(e) => setU({ ...u, password: e.target.value })} />
          </div>
          <div>
            <label>Email</label>
            <input value={u.email} onChange={(e) => setU({ ...u, email: e.target.value })} />
          </div>
          <div>
            <label>Role</label>
            <select value={u.role} onChange={(e) => setU({ ...u, role: e.target.value })}>
              <option value="user">Department User</option>
              <option value="uploader">Department Uploader</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div>
            <label>Department</label>
            <select value={u.department_id} onChange={(e) => setU({ ...u, department_id: e.target.value })}>
              <option value="">None</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="self-end">
            <button className="btn-primary">Create User</button>
          </div>
        </form>

        <table className="table">
          <thead><tr><th>Username</th><th>Role</th><th>Department</th><th>Active</th><th></th></tr></thead>
          <tbody>
            {users.map((usr) => (
              <tr key={usr.id}>
                <td>{usr.username}</td>
                <td><span className="role-badge">{usr.role}</span></td>
                <td>{usr.department_id ? deptName2(usr.department_id) : '—'}</td>
                <td>{usr.is_active ? 'Yes' : 'No'}</td>
                <td><button className="btn-danger" onClick={() => deleteUser(usr.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
