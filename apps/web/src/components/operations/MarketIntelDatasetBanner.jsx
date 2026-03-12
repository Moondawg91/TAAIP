import React from 'react'
import { Alert } from '@mui/material'

export default function MarketIntelDatasetBanner({missing}){
  return (
    <Alert severity="warning" sx={{mb:2, borderRadius:'4px'}}>
      Market Intelligence datasets are not loaded for the selected context. Missing: {Array.isArray(missing)? missing.join(', '): String(missing)}
    </Alert>
  )
}
