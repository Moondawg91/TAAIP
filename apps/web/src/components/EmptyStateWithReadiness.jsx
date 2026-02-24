import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Link, List, ListItem, CircularProgress } from '@mui/material'

function humanize(key){ return String(key).replace(/_/g,' ').replace(/mi /,'Market Intel ').replace(/phonetic/,'Phonetics ') }

export default function EmptyStateWithReadiness({ title, purpose, requiredDatasets = [], templateLinks = [], primaryActions = [] }){
  const [loading, setLoading] = useState(true)
  const [blocking, setBlocking] = useState([])
  useEffect(()=>{
    let cancelled = false
    async function fetchAll(){
      try{
        const mi = await fetch('/api/market-intel/readiness').then(r=>r.json()).catch(()=>null)
        const ph = await fetch('/api/phonetics/readiness').then(r=>r.json()).catch(()=>null)
        const combined = []
        if(mi && mi.blocking) combined.push(...mi.blocking)
        if(ph && ph.blocking) combined.push(...ph.blocking)
        if(!cancelled) setBlocking(combined)
      }finally{ if(!cancelled) setLoading(false) }
    }
    fetchAll()
    return ()=>{ cancelled = true }
  },[])

  const missing = requiredDatasets.filter(d => blocking.includes(d))

  return (
    <Box sx={{ p:2, borderRadius:1, bgcolor:'background.paper', color:'text.primary' }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', mb:1 }}>
        <Box>
          <Typography variant="h6">{title}</Typography>
          {purpose && <Typography variant="caption" sx={{ color:'text.secondary' }}>{purpose}</Typography>}
        </Box>
      </Box>
      <Box sx={{ mt:1 }}>
        {loading ? <CircularProgress size={18} /> : (
          <>
            <Typography variant="body2" sx={{ mb:1 }}>Required datasets:</Typography>
            <List dense>
              {requiredDatasets.map(d => (
                <ListItem key={d} sx={{ py:0 }}>{ humanize(d) } { missing.includes(d) && <strong style={{ color: '#ffb300', marginLeft:8 }}> — Missing</strong> }</ListItem>
              ))}
            </List>

            <Box sx={{ mt:1 }}>
              <Typography variant="body2">How to load data:</Typography>
              {templateLinks.map(t => (
                <Box key={t.href} sx={{ mt:0.5 }}><Link href={t.href}>{t.label || t.href}</Link></Box>
              ))}
            </Box>

            {primaryActions && primaryActions.length>0 && (
              <Box sx={{ mt:1 }}>{primaryActions.map((a,i)=>(<Button key={i} href={a.href} variant="contained" size="small" sx={{ mr:1 }}>{a.label}</Button>))}</Box>
            )}
          </>
        )}
      </Box>
    </Box>
  )
}
