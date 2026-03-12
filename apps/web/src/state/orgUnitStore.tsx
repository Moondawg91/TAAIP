import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { OrgUnitSelection, ActiveUnitContext, UnitOption } from '../types/org'

const STORAGE_KEY = 'taaip_org_selection_v1'

type Store = ActiveUnitContext & {
  setSelection: (next: OrgUnitSelection) => void;
  resetToUSAREC: () => void;
}

const Ctx = createContext<Store | null>(null)

const USAREC: UnitOption = { unit_key: 'USAREC', display_name: 'USAREC', echelon_type: 'CMD' as const }

function deriveActive(selection: OrgUnitSelection) {
  const active = selection.stn || selection.co || selection.bn || selection.bde || selection.cmd
  const activeUnitKey = active.unit_key
  const activeEchelon = (active.echelon_type || 'CMD') as ActiveUnitContext['activeEchelon']
  const parts = [selection.cmd.display_name]
  if (selection.bde) parts.push(selection.bde.display_name)
  if (selection.bn) parts.push(selection.bn.display_name)
  if (selection.co) parts.push(selection.co.display_name)
  if (selection.stn) parts.push(selection.stn.display_name)
  const pathLabel = parts.join(' > ')
  return { selection, activeUnitKey, activeEchelon, pathLabel }
}

export function OrgUnitStoreProvider({ children }: { children: React.ReactNode }){
  const [selection, setSelectionInternal] = useState<OrgUnitSelection>(()=>{
    try{
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) return JSON.parse(raw)
    }catch(e){}
    return { cmd: USAREC, bde: null, bn: null, co: null, stn: null }
  })

  useEffect(()=>{
    try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(selection)) }catch(e){}
  }, [selection])

  const setSelection = (next: OrgUnitSelection) => setSelectionInternal(next)

  const resetToUSAREC = () => setSelectionInternal({ cmd: USAREC, bde: null, bn: null, co: null, stn: null })

  const derived = useMemo(()=> deriveActive(selection), [selection])

  const store: Store = {
    ...derived,
    setSelection,
    resetToUSAREC
  }

  return <Ctx.Provider value={store}>{children}</Ctx.Provider>
}

export function useOrgUnitStore(){
  const s = useContext(Ctx)
  if (!s) throw new Error('useOrgUnitStore must be used within OrgUnitStoreProvider')
  return s
}

export default Ctx
