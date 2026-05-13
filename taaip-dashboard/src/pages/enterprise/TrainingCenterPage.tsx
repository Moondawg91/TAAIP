import React from 'react';
import { Card } from '../../components/shared/ui';
import { TAAIP_DOCTRINE } from '../../config/taaipDoctrine';
import LMSHub from '../../components/LMSHub';

export const TrainingCenterPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card title="Training Center">
        <p className="text-sm text-slate-300">
          Doctrine and skills delivery includes UTCs + TOR + SRP/ROP/TWG references and role-based readiness paths.
        </p>
        <ul className="mt-3 text-sm text-slate-300 list-disc list-inside">
          {TAAIP_DOCTRINE.doctrineLibraries.map((topic) => (
            <li key={topic}>{topic}</li>
          ))}
        </ul>
      </Card>
      <LMSHub />
    </div>
  );
};

export default TrainingCenterPage;
