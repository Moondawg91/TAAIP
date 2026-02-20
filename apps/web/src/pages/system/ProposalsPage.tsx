import React, { useEffect, useState } from 'react'
import apiClient from '../../api/client'

export default function ProposalsPage(){
  const [proposals, setProposals] = useState([])
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')

  async function load(){
    try{ const res = await apiClient.listProposals() ; setProposals(res || []) }catch(e){ setProposals([]) }
  }

  useEffect(()=>{ load() }, [])

  async function create(){
    if(!title) return
    try{
      await apiClient.createProposal({ title, description: desc })
      setTitle('')
      setDesc('')
      await load()
    }catch(e){ console.error(e) }
  }

  async function submit(id){
    try{ await apiClient.submitProposal(id); await load() }catch(e){ console.error(e) }
  }

  async function review(id){
    const note = window.prompt('Review note (approve/reject):')
    if(note===null) return
    try{ await apiClient.reviewProposal(id, { note }); await load() }catch(e){ console.error(e) }
  }

  return (
    <div style={{padding:20}}>
      <h2>Proposals</h2>
      <div style={{marginBottom:12}}>
        <input placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} style={{width:'40%', marginRight:8}} />
        <input placeholder="Short description" value={desc} onChange={e=>setDesc(e.target.value)} style={{width:'40%'}} />
        <button onClick={create} style={{marginLeft:8}}>Create</button>
      </div>
      <div>
        <ul>
          {(proposals||[]).map(p=> (
            <li key={p.id || JSON.stringify(p)}>
              <strong>{p.title || p.name}</strong> — {p.status || p.state || ''}
              <div style={{display:'inline-block', marginLeft:8}}>
                <button onClick={()=>submit(p.id)} style={{marginRight:6}}>Submit</button>
                <button onClick={()=>review(p.id)}>Review</button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
