import React from 'react'
import OrgUnitCascade from './OrgUnitCascade'
import { useOrgUnitStore } from '../state/orgUnitStore'
import { getOrgChildren } from '../api/org'

export default function UnitFilterBar(){
  const store = useOrgUnitStore()
  const { selection, setSelection } = store

  return (
    <div style={{ padding: 10, borderBottom: '1px solid rgba(0,0,0,0.06)', background: 'transparent' }}>
      <OrgUnitCascade
        value={selection}
        onChange={(next)=> setSelection(next)}
        fetchChildren={getOrgChildren as any}
        showRSIDSecondary={false}
      />
    </div>
  )
}
