import React from 'react';

interface ProjectEditorProps {
  projectId: string | null;
  onClose: () => void;
}

export const ProjectEditor: React.FC<ProjectEditorProps> = ({ projectId, onClose }) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Project editor</h3>
          <p className="text-sm text-slate-600">Selected project: {projectId || 'No project selected'}</p>
        </div>
        <button onClick={onClose} className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800">
          Close
        </button>
      </div>
      <p className="mt-4 text-sm text-slate-700">Use the connected commander workflow to manage operational actions and refresh authoritative data.</p>
    </div>
  );
};

export default ProjectEditor;
