import React from 'react';

interface CreateProjectModalProps {
  onClose: () => void;
}

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({ onClose }) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Create project</h3>
          <p className="text-sm text-slate-600">Project creation remains available from the admin console.</p>
        </div>
        <button onClick={onClose} className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800">
          Close
        </button>
      </div>
      <p className="mt-4 text-sm text-slate-700">This placeholder keeps the legacy management surface build-safe during the commander workflow consolidation.</p>
    </div>
  );
};

export default CreateProjectModal;
