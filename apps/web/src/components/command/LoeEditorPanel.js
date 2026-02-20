import React, {useEffect, useState} from 'react'
import api from '../../api/client'

export default function LoeEditorPanel(){
  const [loes, setLoes] = useState([])
  const [title, setTitle] = useState('')

  useEffect(()=>{
    let mounted = true
    api.listCommandCenterLoes().then(r=>{ if(mounted && r && r.items) setLoes(r.items) }).catch(()=>{})
    return ()=>{ mounted=false }
  }, [])

  const add = async ()=>{
    if(!title) return
    await api.createCommandCenterLoe({id: `loe-${Date.now()}`, title, description: ''})
    setTitle('')
    const r = await api.listCommandCenterLoes()
    if(r && r.items) setLoes(r.items)
  }

  return (
    <div style={{padding:12}}>
      <h4 style={{color:'#fff', marginTop:0}}>Lines of Effort</h4>
      <div style={{display:'flex', gap:8}}>
        <input value={title} onChange={e=>setTitle(e.target.value)} placeholder='New LOE title' />
        <button onClick={add}>Add LOE</button>
      </div>
      <ul>
        {loes.map(l=> <li key={l.id} style={{color:'#fff'}}>{l.title}</li>)}
      </ul>
    </div>
  )
}
