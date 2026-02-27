import React, { createContext, useContext, useState, useEffect } from 'react'
import { getSelection, setSelection as storeSetSelection, clearLowerLevels } from '../store/orgSelection'

const OrgSelectionContext = createContext(null)

export function OrgSelectionProvider({ children }){
  const [selection, setSelectionState] = useState(getSelection())

  useEffect(()=>{
    // ensure persisted selection exists on mount
    const cur = getSelection()
    setSelectionState(cur)
  }, [])

  function _applyAndSet(next){
    const normalized = storeSetSelection(next)
    setSelectionState(normalized)
    return normalized
  }

  function setBde(bdeObj){
    const next = Object.assign({}, selection, { bde: bdeObj, bn: null, co: null, stn: null })
    return _applyAndSet(next)
  }

  function setBn(bnObj){
    const next = Object.assign({}, selection, { bn: bnObj, co: null, stn: null })
    return _applyAndSet(next)
  }

  function setCo(coObj){
    const next = Object.assign({}, selection, { co: coObj, stn: null })
    return _applyAndSet(next)
  }

  function setStn(stnObj){
    const next = Object.assign({}, selection, { stn: stnObj })
    return _applyAndSet(next)
  }

  function resetToUsarec(){
    const next = { root_rsid: 'USAREC', bde: null, bn: null, co: null, stn: null }
    return _applyAndSet(next)
  }

  function setSelection(updater){
    const next = (typeof updater === 'function') ? updater(selection) : updater
    return _applyAndSet(next)
  }

  return (
    <OrgSelectionContext.Provider value={{ selection, setSelection, setBde, setBn, setCo, setStn, resetToUsarec }}>
      {children}
    </OrgSelectionContext.Provider>
  )
}

export function useOrgSelection(){
  const ctx = useContext(OrgSelectionContext)
  if (!ctx) throw new Error('useOrgSelection must be used within OrgSelectionProvider')
  return ctx
}

export default OrgSelectionContext
