import React from 'react'
import { Box, Typography, List, ListItem } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import EmptyState from '../../components/common/EmptyState'

export default function UpcomingItems(){
  const theme = useTheme()
  const items: any[] = []
  const panelBg = theme.palette.mode === 'dark' ? 'background.paper' : '#0f1720'
  return (
    <Box sx={{ p:2, bgcolor: panelBg, borderRadius: '4px' }}>
      <Typography variant="h6" sx={{ mb:1 }}>Upcoming Items</Typography>
      <List sx={{ p:0, maxHeight:220, overflow:'auto' }}>
        {items.length === 0 ? (
          <ListItem>
            <EmptyState title="No upcoming items" subtitle="" />
          </ListItem>
        ) : items.map(it => (
          <ListItem key={it.id}>{it.title}</ListItem>
        ))}
      </List>
    </Box>
  )
}
