import React from 'react'
import { Tabs, Tab, Box } from '@mui/material'
import { useSearchParams } from 'react-router-dom'
import { defaultViewForRoles } from '../utils/roleHelper'

type Props = {
  roles?: string[]
}

export default function DualModeTabs({roles = []}: Props){
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('view') || defaultViewForRoles(roles)

  function handleChange(_e:any, val:string){
    const sp = new URLSearchParams(searchParams.toString())
    sp.set('view', val)
    setSearchParams(sp)
  }

  return (
    <Box sx={{borderBottom:1, borderColor:'divider', mb:2}}>
      <Tabs value={q} onChange={handleChange}>
        <Tab value="executive" label="Executive" />
        <Tab value="comptroller" label="Comptroller" />
      </Tabs>
    </Box>
  )
}
