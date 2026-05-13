import React, { useState } from 'react';
import { SystemControlPage, SystemControlTab } from './SystemControlPage';

export const AdminConsole: React.FC = () => {
  type AdminView =
    | 'dashboard'
    | 'system-control'
    | 'user-role-management'
    | 'helpdesk'
    | 'database-management'
    | 'system-backup'
    | 'database-sync'
    | 'audit-reports';

  const [activeView, setActiveView] = useState<AdminView>('dashboard');
  const [systemControlInitialTab, setSystemControlInitialTab] = useState<SystemControlTab>('activity_logs');

  const isAdmin = true;

  const cards: Array<{ id: string; title: string; subtitle: string; action: () => void }> = [
    {
      id: 'user-role-management',
      title: 'User & Role Management',
      subtitle: 'Manage user accounts and permission roles',
      action: () => setActiveView('user-role-management'),
    },
    {
      id: 'helpdesk',
      title: 'Helpdesk',
      subtitle: 'Review support tickets and request workflows',
      action: () => setActiveView('helpdesk'),
    },
    {
      id: 'system-control',
      title: 'System Control',
      subtitle: 'Access logs, maintenance windows, and platform health',
      action: () => {
        setSystemControlInitialTab('activity_logs');
        setActiveView('system-control');
      },
    },
    {
      id: 'database-management',
      title: 'Database Management (McLeod)',
      subtitle: 'Manage McLeod data lifecycle and maintenance actions',
      action: () => setActiveView('database-management'),
    },
    {
      id: 'system-update-logs',
      title: 'System Update Logs',
      subtitle: 'Open update release history and approval status',
      action: () => {
        setSystemControlInitialTab('update_logs');
        setActiveView('system-control');
      },
    },
    {
      id: 'system-backup',
      title: 'System Backup',
      subtitle: 'View backup coverage and backup operations',
      action: () => setActiveView('system-backup'),
    },
    {
      id: 'database-sync',
      title: 'Database Sync',
      subtitle: 'Monitor synchronization jobs and health status',
      action: () => setActiveView('database-sync'),
    },
    {
      id: 'audit-reports',
      title: 'Audit Reports',
      subtitle: 'Inspect compliance and operational audit reporting',
      action: () => setActiveView('audit-reports'),
    },
  ];

  const visibleCards = isAdmin ? cards : cards.filter((card) => card.id !== 'database-management');

  if (activeView === 'system-control') {
    return (
      <SystemControlPage
        initialTab={systemControlInitialTab}
        onBack={() => setActiveView('dashboard')}
      />
    );
  }

  const placeholderTitle: Record<Exclude<AdminView, 'dashboard' | 'system-control'>, string> = {
    'user-role-management': 'User & Role Management',
    helpdesk: 'Helpdesk',
    'database-management': 'Database Management (McLeod)',
    'system-backup': 'System Backup',
    'database-sync': 'Database Sync',
    'audit-reports': 'Audit Reports',
  };

  if (activeView !== 'dashboard') {
    return (
      <div className="min-h-screen p-6" style={{ background: '#081B33' }}>
        <div className="mb-5">
          <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">{placeholderTitle[activeView]}</h1>
          <p className="mt-1 text-[12px] text-[#64748B]">Admin function view</p>
        </div>

        <div className="rounded-md border border-[#1D3A5C] bg-[#0E2847] p-6">
          <p className="text-[13px] text-[#94A3B8]">
            This section is prepared as a placeholder for the selected admin function.
          </p>
          <button
            onClick={() => setActiveView('dashboard')}
            className="mt-4 rounded-md border border-[#1D3A5C] bg-transparent px-3 py-1.5 text-[12px] font-semibold text-[#60A5FA] hover:text-[#F3F5F7]"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" style={{ background: '#081B33' }}>
      <div className="mb-5">
        <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Admin Console</h1>
        <p className="text-[12px] text-[#64748B]">System administration and operational controls</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {visibleCards.slice(0, 5).map((card) => (
          <button
            key={card.id}
            onClick={card.action}
            className="rounded-md border border-[#1D3A5C] bg-[#0E2847] p-4 text-left transition hover:bg-[#142F52]"
          >
            <h3 className="text-[13px] font-semibold text-[#F3F5F7]">{card.title}</h3>
            <p className="mt-2 text-[12px] text-[#94A3B8]">{card.subtitle}</p>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 mt-6">
        {visibleCards.slice(5, 8).map((card) => (
          <button
            key={card.id}
            onClick={card.action}
            className="rounded-md border border-[#1D3A5C] bg-[#0E2847] p-4 text-left transition hover:bg-[#142F52]"
          >
            <h3 className="text-[13px] font-semibold text-[#F3F5F7]">{card.title}</h3>
            <p className="mt-2 text-[12px] text-[#94A3B8]">{card.subtitle}</p>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AdminConsole;
