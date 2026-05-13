import { EnterprisePageId } from '../../config/enterprisePages';

export type OperationalRole =
  | 'recruiter'
  | 'station-commander'
  | 'company-staff'
  | 'bn-staff'
  | 'bde-staff'
  | 'usarec-hq'
  | '420t'
  | 'admin';

export type VisibilityTier = 'station' | 'company' | 'battalion' | 'brigade' | 'enterprise';

export interface AccessProfile {
  role: OperationalRole;
  tier: VisibilityTier;
  allowedPages: EnterprisePageId[];
  allowedDataDomains: string[];
}
