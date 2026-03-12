import React, { createContext, useContext, useEffect, useState } from 'react'

type ScopeCtx = { scope: string | null; setScope: (s: string|null)=>void }
const Ctx = createContext<ScopeCtx>({ scope: null, setScope: ()=>{} })

export function ScopeProvider({ children }: { children: React.ReactNode }){
  const [scope, setScope] = useState<string|null>(()=>{
    try{
      return localStorage.getItem('taaip_scope')
    }catch{ return null }
  })
  useEffect(()=>{ try{ if(scope===null) localStorage.removeItem('taaip_scope'); else localStorage.setItem('taaip_scope', scope) }catch{} }, [scope])
  return <Ctx.Provider value={{ scope, setScope }}>{children}</Ctx.Provider>
}

export function useScope(){ return useContext(Ctx) }

// New convenience wrapper: prefer `useEchelon()` in UI code to express visible naming
export function useEchelon(){ const ctx = useContext(Ctx); return { echelon: ctx.scope, setEchelon: ctx.setScope } }

export default Ctx
