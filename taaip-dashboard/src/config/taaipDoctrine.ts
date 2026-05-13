export const TAAIP_DOCTRINE = {
  srpPriorityOrder: ['seniors', 'juniors', 'post-secondary'] as const,
  segmentation: ['ZIP', 'CBSA', 'PRIZM'] as const,
  uncontactedLeadSignals: ['ITEMLC', 'APPLEMDT'] as const,
  dodComponents: ['Army', 'Navy', 'Air Force', 'Marines', 'Space Force', 'Coast Guard', 'Reserve', 'National Guard'] as const,
  ingestionFeeds: ['Vantage', 'AIE', 'DoD Component Data', 'SharePoint'] as const,
  doctrineLibraries: ['USAREC Regulations', 'USAREC Messages', 'UTCs', 'TOR', 'SRP', 'ROP', 'TWG'] as const,
} as const;

export type DoctrineVisibilityTier = 'Recruiter' | 'Company' | 'BN' | 'BDE' | 'USAREC';

export const VISIBILITY_TIERS: DoctrineVisibilityTier[] = ['Recruiter', 'Company', 'BN', 'BDE', 'USAREC'];
