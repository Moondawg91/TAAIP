import React from 'react'

export default function ZeroStatePanel({title, message}){
  return (
    <div style={{padding:16, border:'1px dashed rgba(255,255,255,0.06)', borderRadius:6, background:'transparent'}}>
      <h3 style={{margin:'0 0 8px 0', color:'#fff'}}>{title}</h3>
      <div style={{color:'rgba(255,255,255,0.7)'}}>{message}</div>
    </div>
  )
}
