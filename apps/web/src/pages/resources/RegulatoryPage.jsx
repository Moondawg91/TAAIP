import React, {useEffect, useState} from 'react'
import { Box, Container, Paper, Typography, TextField, Select, MenuItem, List, ListItem, ListItemText, Collapse, IconButton } from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { getRegulatoryReferences } from '../../api/client'

export default function RegulatoryPage(){
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [items, setItems] = useState([])
  const [openIds, setOpenIds] = useState({})

  async function load(){
    try{
      const qs = {}
      if(search) qs.search = search
      if(category) qs.category = category
      const r = await getRegulatoryReferences(qs)
      setItems(r.items || [])
    }catch(e){ setItems([]) }
  }

  useEffect(()=>{ load() }, [])

  return (
    <Container maxWidth="lg" sx={{py:2}}>
      <Typography variant="h5" sx={{mb:2}}>Regulatory References</Typography>

      <Paper sx={{p:1, mb:2, display:'flex', gap:1, alignItems:'center', bgcolor:'transparent', borderRadius:'4px'}}>
        <TextField size="small" placeholder="Search" value={search} onChange={e=>setSearch(e.target.value)} onBlur={load} sx={{minWidth:240}} />
        <Select value={category} size="small" onChange={e=>{ setCategory(e.target.value); setTimeout(load,10) }} sx={{minWidth:180}}>
          <MenuItem value="">All Categories</MenuItem>
          <MenuItem value={'Operations'}>Operations</MenuItem>
          <MenuItem value={'Market'}>Market</MenuItem>
          <MenuItem value={'Processing'}>Processing</MenuItem>
          <MenuItem value={'Training'}>Training</MenuItem>
          <MenuItem value={'Governance'}>Governance</MenuItem>
        </Select>
      </Paper>

      <Paper sx={{p:1, bgcolor:'transparent', borderRadius:'4px'}}>
        <List>
          {items.map(it=> (
            <Box key={it.id} sx={{borderBottom:'1px solid rgba(255,255,255,0.04)', py:1}}>
              <ListItem disableGutters secondaryAction={
                <IconButton edge="end" onClick={()=> setOpenIds(s=>({...s, [it.id]: !s[it.id]}))} sx={{color:'text.secondary'}}>
                  <ExpandMoreIcon />
                </IconButton>
              }>
                <ListItemText primary={`${it.code} — ${it.title}`} secondary={it.category} primaryTypographyProps={{variant:'body1'}} />
              </ListItem>
              <Collapse in={!!openIds[it.id]} timeout="auto" unmountOnExit>
                <Box sx={{p:1}}>
                  <Typography variant="body2" sx={{color:'text.secondary'}}>{it.description}</Typography>
                  <Typography variant="caption" sx={{display:'block', mt:1, color:'text.secondary'}}>Authority: {it.authority_level}</Typography>
                </Box>
              </Collapse>
            </Box>
          ))}
        </List>
      </Paper>
    </Container>
  )
}
