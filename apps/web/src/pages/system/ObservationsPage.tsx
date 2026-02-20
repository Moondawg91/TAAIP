import React, { useEffect, useState } from 'react'
import apiClient from '../../api/client'

export default function ObservationsPage(){
  const [observations, setObservations] = useState([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)

  async function load(){
    setLoading(true)
    try{ const res = await apiClient.listSystemObservations() ; setObservations(res || []) }catch(e){ setObservations([]) }
    setLoading(false)
  }

  useEffect(()=>{ load() }, [])

  async function submit(){
    if(!text) return
    try{
      await apiClient.postSystemObservation({ text })
      setText('')
      await load()
    }catch(e){ console.error(e) }
  }

  return (
    <div style={{padding:20}}>
      <h2>System Observations</h2>
      <div>
        <input style={{width:'60%'}} value={text} onChange={e=>setText(e.target.value)} placeholder="Write an observation" />
        <button onClick={submit} style={{marginLeft:8}}>Submit</button>
      </div>
      <div style={{marginTop:16}}>
        {loading ? (<div>Loading...</div>) : (
          <ul>
            {(observations || []).map(o=> (
              <li key={o.id || JSON.stringify(o)}>{o.text || o.note || JSON.stringify(o)}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
