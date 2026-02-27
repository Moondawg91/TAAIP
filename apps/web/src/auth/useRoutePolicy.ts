import { useLocation } from 'react-router-dom'
import ROUTE_POLICIES, { RoutePolicy } from './routePolicy'

function findPolicy(pathname: string): RoutePolicy | null {
  if (!pathname) return null
  // find the longest matching prefix
  let best: RoutePolicy | null = null
  for (const p of ROUTE_POLICIES) {
    if (!p || !p.path) continue
    if (pathname === p.path || pathname.startsWith(p.path)) {
      if (!best || p.path.length > best.path.length) best = p
    }
  }
  return best
}

export default function useRoutePolicy(){
  const loc = useLocation()
  const policy = findPolicy(loc.pathname || '')
  return policy || null
}
