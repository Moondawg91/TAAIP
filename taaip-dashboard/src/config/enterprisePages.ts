import { Permission } from '../types/auth';

export type EnterprisePageId =
  | 'home-page'
  | 'command-center'
  | 'fusion-cell'
  | 'twg'
  | 'targeting-board'
  | 'operations-page'
  | 'field-activities-page'
  | 'budget-page'
  | 'market-intelligence'
  | 'school-intelligence'
  | 'dod-market-share'
  | 'segmentation'
  | 'reserve-alignment'
  | 'market-potential'
  | 'out-of-area-analysis'
  | 'roi-analysis'
  | 'performance-page'
  | 'funnel-analysis'
  | 'data-document-center'
  | 'training-center'
  | 'admin';

export interface EnterprisePageDefinition {
  id: EnterprisePageId;
  label: string;
  requiredPermissions: Permission[];
}

export const ENTERPRISE_PAGES: EnterprisePageDefinition[] = [
  { id: 'home-page', label: 'Home Page', requiredPermissions: ['view_all_dashboards'] },
  { id: 'command-center', label: 'Command Center', requiredPermissions: ['view_analytics'] },
  { id: 'fusion-cell', label: 'Fusion Cell', requiredPermissions: ['view_twg'] },
  { id: 'twg', label: 'TWG', requiredPermissions: ['view_twg'] },
  { id: 'targeting-board', label: 'Targeting Board', requiredPermissions: ['view_tdb'] },
  { id: 'operations-page', label: 'Operations', requiredPermissions: ['view_twg'] },
  { id: 'field-activities-page', label: 'Field Activities', requiredPermissions: ['create_events'] },
  { id: 'budget-page', label: 'Budget', requiredPermissions: ['view_budget'] },
  { id: 'market-intelligence', label: 'Market Intelligence', requiredPermissions: ['view_market_data'] },
  { id: 'school-intelligence', label: 'School Intelligence', requiredPermissions: ['view_market_data'] },
  { id: 'dod-market-share', label: 'DoD Market Share', requiredPermissions: ['view_market_data'] },
  { id: 'segmentation', label: 'Segmentation', requiredPermissions: ['view_market_data'] },
  { id: 'reserve-alignment', label: 'Reserve Alignment', requiredPermissions: ['view_market_data'] },
  { id: 'market-potential', label: 'Market Potential', requiredPermissions: ['view_market_data'] },
  { id: 'out-of-area-analysis', label: 'Out-of-Area Analysis', requiredPermissions: ['view_market_data'] },
  { id: 'roi-analysis', label: 'ROI Analysis Page', requiredPermissions: ['view_analytics'] },
  { id: 'performance-page', label: 'Performance Page', requiredPermissions: ['view_analytics'] },
  { id: 'funnel-analysis', label: 'Funnel Analysis Page', requiredPermissions: ['view_analytics'] },
  { id: 'data-document-center', label: 'Data & Document Center', requiredPermissions: ['upload_data'] },
  { id: 'training-center', label: 'Training Center', requiredPermissions: ['view_analytics'] },
  { id: 'admin', label: 'Admin', requiredPermissions: ['system_admin'] },
];
