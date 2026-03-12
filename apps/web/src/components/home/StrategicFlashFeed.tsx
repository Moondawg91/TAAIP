import React from 'react'
import { Box, Typography, List, ListItem, Chip } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import EmptyState from '../../components/common/EmptyState'

export default function StrategicFlashFeed(){
  const theme = useTheme()
  // Empty-safe component — backend integration later
  const items: any[] = []
  const tags = ['USAREC Ops','420T','Policy','Systems']
  const panelBg = theme.palette.mode === 'dark' ? 'background.paper' : '#0f1720'
  return (
    <Box sx={{ p:2, bgcolor: panelBg, borderRadius: '4px' }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', mb:1 }}>
        <Typography variant="h6">Strategic Flash Feed</Typography>
        <Box>
          {tags.map(t=> <Chip key={t} label={t} size="small" sx={{ ml:0.5, bgcolor: 'transparent', color: 'text.secondary' }} />)}
        </Box>
      </Box>
      <List sx={{ p:0, maxHeight:200, overflow:'auto' }}>
        {items.length === 0 ? (
          <ListItem>
            <EmptyState title="No updates loaded" subtitle="" />
          </ListItem>
        ) : items.map(i => (
          <ListItem key={i.id}>{i.title}</ListItem>
        ))}
      </List>
    </Box>
  )
}
