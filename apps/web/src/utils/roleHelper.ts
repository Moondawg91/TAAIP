export function canViewComptroller(userRoles: string[] = []){
  if(!Array.isArray(userRoles)) return false
  const allowed = ['TAWO','A&PA','COMPTROLLER']
  return userRoles.some(r => allowed.includes(r))
}

export function defaultViewForRoles(userRoles: string[] = []){
  return canViewComptroller(userRoles) ? 'comptroller' : 'executive'
}
