import { defaultViewForRoles, canViewComptroller } from '../utils/roleHelper'

describe('DualModeTabs helper behavior', () => {
  it('returns comptroller for comptroller roles', () => {
    expect(canViewComptroller(['COMPTROLLER'])).toBe(true)
    expect(defaultViewForRoles(['COMPTROLLER'])).toBe('comptroller')
  })
  it('returns executive for other roles', () => {
    expect(canViewComptroller(['USER'])).toBe(false)
    expect(defaultViewForRoles(['USER'])).toBe('executive')
  })
})
