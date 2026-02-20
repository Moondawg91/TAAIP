import React from 'react'

export default function ExportMenuButton({onExportJson, onExportCsv}){
  return (
    <div style={{display:'flex', gap:8}}>
      <button onClick={onExportCsv} style={{padding:'6px 10px'}}>Export CSV</button>
      <button onClick={onExportJson} style={{padding:'6px 10px'}}>Export JSON</button>
    </div>
  )
}
