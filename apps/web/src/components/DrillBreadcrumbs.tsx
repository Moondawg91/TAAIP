import React from 'react'
import { Breadcrumbs, Link, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'

type Trail = {label:string, to?:string}

export default function DrillBreadcrumbs({trail}:{trail:Trail[]}){
  const nav = useNavigate()
  return (
    <Breadcrumbs aria-label="breadcrumb" sx={{mb:1}}>
      {trail.map((t,i)=> t.to ? (
        <Link key={i} onClick={()=>nav(t.to!)} sx={{cursor:'pointer'}}>{t.label}</Link>
      ) : (
        <Typography key={i} color="text.primary">{t.label}</Typography>
      ))}
    </Breadcrumbs>
  )
}
