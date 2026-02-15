import React, {useState} from 'react'
import axios from 'axios'

export default function App(){
  const [username, setUsername] = useState('')
  const [token, setToken] = useState(null)
  const [scope, setScope] = useState(null)
  const [coverage, setCoverage] = useState(null)
  const [rsid, setRsid] = useState('1A1D')

  const login = async ()=>{
    const res = await axios.post('/api/auth/login', {username})
    setToken(res.data.token)
    setScope(res.data.scope)
  }

  const loadCoverage = async ()=>{
    if(!token) return alert('login first')
    const res = await axios.get(`/api/org/stations/${rsid}/zip-coverage`, {headers: {Authorization: `Bearer ${token}`}})
    setCoverage(res.data)
  }

  return (
    <div style={{padding:20}}>
      <h1>TAAIP - Command Center (Phase 1)</h1>
      <div>
        <input placeholder="username" value={username} onChange={e=>setUsername(e.target.value)} />
        <button onClick={login}>Login</button>
        <span style={{marginLeft:10}}>scope: {scope}</span>
      </div>

      <div style={{marginTop:20}}>
        <h3>ZIP Coverage</h3>
        <input value={rsid} onChange={e=>setRsid(e.target.value)} />
        <button onClick={loadCoverage}>Load</button>
        <pre>{coverage ? JSON.stringify(coverage, null, 2) : 'No data'}</pre>
      </div>
    </div>
  )
}
