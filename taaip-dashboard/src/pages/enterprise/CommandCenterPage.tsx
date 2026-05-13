import React from 'react';
import { CommandCenterDashboard } from '../../components/CommandCenterDashboard';
import { EnterpriseExportEngine } from './EnterpriseExportEngine';

interface Props { onNavigate: (tab: string) => void }

export const CommandCenterPage: React.FC<Props> = ({ onNavigate }) => {
  return (
    <div className="space-y-6">
      <CommandCenterDashboard onNavigate={onNavigate} />
      <EnterpriseExportEngine />
    </div>
  );
};

export default CommandCenterPage;
