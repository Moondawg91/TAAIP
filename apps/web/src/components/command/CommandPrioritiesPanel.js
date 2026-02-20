import React, {useEffect, useState} from 'react'
import api from '../../api/client'

export default function CommandPrioritiesPanel(){
  const [items, setItems] = useState([])

  useEffect(()=>{
    let mounted = true
    api.getCommandCenterPriorities().then(r=>{ if(mounted && r && r.items) setItems(r.items) }).catch(()=>{})
    return ()=>{ mounted=false }
  }, [])

  return (
    <div style={{padding:12}}>
      <h4 style={{color:'#fff', marginTop:0}}>Command Priorities</h4>
      {items.length===0 ? <div style={{color:'rgba(255,255,255,0.6)'}}>No priorities yet.</div> : (
        <ul>
          {items.map(it=> <li key={it.id} style={{color:'#fff'}}>{it.title}</li>)}
        </ul>
      )}
    </div>
  )
}
