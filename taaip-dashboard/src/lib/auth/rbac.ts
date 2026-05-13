import { ENTERPRISE_PAGES, EnterprisePageId } from '../../config/enterprisePages';
import { User } from '../../types/auth';
import { AccessProfile, OperationalRole } from './types';

const ALL_PAGES = ENTERPRISE_PAGES.map((page) => page.id);

const BASE_PROFILES: Record<OperationalRole, AccessProfile> = {
  'recruiter': {
    role: 'recruiter',
    tier: 'station',
    allowedPages: ['home-page', 'field-activities-page', 'training-center', 'data-document-center'],
    allowedDataDomains: ['station', 'document_center'],
  },
  'station-commander': {
    role: 'station-commander',
    tier: 'station',
    allowedPages: ['home-page', 'command-center', 'operations-page', 'field-activities-page', 'funnel-analysis', 'performance-page', 'training-center', 'data-document-center'],
    allowedDataDomains: ['station', 'company', 'document_center'],
  },
  'company-staff': {
    role: 'company-staff',
    tier: 'company',
    allowedPages: ['home-page', 'command-center', 'fusion-cell', 'twg', 'targeting-board', 'operations-page', 'field-activities-page', 'budget-page', 'market-intelligence', 'school-intelligence', 'dod-market-share', 'segmentation', 'reserve-alignment', 'market-potential', 'out-of-area-analysis', 'roi-analysis', 'performance-page', 'funnel-analysis', 'data-document-center', 'training-center'],
    allowedDataDomains: ['company', 'battalion', 'document_center', 'market_intelligence'],
  },
  'bn-staff': {
    role: 'bn-staff',
    tier: 'battalion',
    allowedPages: [...ALL_PAGES.filter((id) => id !== 'admin')],
    allowedDataDomains: ['battalion', 'brigade', 'document_center', 'market_intelligence', 'admin_read'],
  },
  'bde-staff': {
    role: 'bde-staff',
    tier: 'brigade',
    allowedPages: [...ALL_PAGES.filter((id) => id !== 'admin')],
    allowedDataDomains: ['brigade', 'enterprise', 'document_center', 'market_intelligence', 'admin_read'],
  },
  'usarec-hq': {
    role: 'usarec-hq',
    tier: 'enterprise',
    allowedPages: [...ALL_PAGES.filter((id) => id !== 'admin')],
    allowedDataDomains: ['enterprise', 'document_center', 'market_intelligence', 'admin_read'],
  },
  '420t': {
    role: '420t',
    tier: 'enterprise',
    allowedPages: [...ALL_PAGES],
    allowedDataDomains: ['enterprise', 'document_center', 'market_intelligence', 'admin_control'],
  },
  'admin': {
    role: 'admin',
    tier: 'enterprise',
    allowedPages: [...ALL_PAGES],
    allowedDataDomains: ['enterprise', 'document_center', 'market_intelligence', 'admin_control'],
  },
};

export function resolveOperationalRole(user: User): OperationalRole {
  const position = user.position.toLowerCase();
  if (position.includes('admin')) return 'admin';
  if (position.includes('420t')) return '420t';
  if (position.includes('usarec')) return 'usarec-hq';
  if (position.includes('bde')) return 'bde-staff';
  if (position.includes('bn')) return 'bn-staff';
  if (position.includes('company')) return 'company-staff';
  if (position.includes('station')) return 'station-commander';
  return 'recruiter';
}

export function getAccessProfileForUser(user: User): AccessProfile {
  const role = resolveOperationalRole(user);
  return BASE_PROFILES[role];
}

export function canAccessEnterprisePage(user: User, pageId: EnterprisePageId): boolean {
  return getAccessProfileForUser(user).allowedPages.includes(pageId);
}

export function filterDataByTier<T extends Record<string, unknown>>(
  user: User,
  rows: T[],
  key: keyof T,
): T[] {
  const profile = getAccessProfileForUser(user);
  if (profile.tier === 'enterprise') {
    return rows;
  }
  return rows.filter((row) => {
    const value = String(row[key] ?? '').toLowerCase();
    if (profile.tier === 'brigade') return value.includes('bde') || value.includes('bn') || value.includes('company') || value.includes('station');
    if (profile.tier === 'battalion') return value.includes('bn') || value.includes('company') || value.includes('station');
    if (profile.tier === 'company') return value.includes('company') || value.includes('station');
    return value.includes('station');
  });
}
