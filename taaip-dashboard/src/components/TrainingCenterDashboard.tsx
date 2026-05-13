import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Filter, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';

type TabKey = 'courses' | 'learning_paths' | 'certifications';

type Course = {
  course_id: string;
  course_name: string;
  description: string;
  learning_objectives: string[];
  modules: string[];
  category: string;
  level: string;
  duration: string;
  owner: string;
  last_updated: string;
  status: string;
};

type LearningPath = {
  path_id: string;
  path_name: string;
  role: string;
  courses_count: number;
  estimated_duration: string;
  completion_rate: number;
  status: string;
  overview: string;
  required_courses: string[];
  progress_tracking: string;
  completion_percent: number;
};

type Certification = {
  certification_id: string;
  certification_name: string;
  role: string;
  requirements: string;
  validity_period: string;
  status: string;
  completion_status: string;
  expiration_tracking: string;
  renewal_requirements: string;
};

type Filters = {
  categories: string[];
  levels: string[];
  roles: string[];
  statuses: string[];
};

type Payload = {
  data_as_of: string;
  active_tab: TabKey;
  courses: Course[];
  learning_paths: LearningPath[];
  certifications: Certification[];
  filters: Filters;
};

const EMPTY_FILTERS: Filters = { categories: [], levels: [], roles: [], statuses: [] };

const fmtPct = (v: number | null | undefined): string => {
  const n = Number(v ?? 0);
  if (!Number.isFinite(n)) return '0%';
  return `${Math.round(n)}%`;
};

export const TrainingCenterDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<TabKey>('courses');
  const [category, setCategory] = useState('');
  const [level, setLevel] = useState('');
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');

  const [dataAsOf, setDataAsOf] = useState('');
  const [courses, setCourses] = useState<Course[]>([]);
  const [learningPaths, setLearningPaths] = useState<LearningPath[]>([]);
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);

  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null);
  const [selectedPathId, setSelectedPathId] = useState<string | null>(null);
  const [selectedCertId, setSelectedCertId] = useState<string | null>(null);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set('tab', activeTab);
      if (category) params.set('category', category);
      if (level) params.set('level', level);
      if (role) params.set('role', role);
      if (status) params.set('status', status);
      if (search) params.set('search', search);

      const res = await fetch(`${API_BASE}/api/v2/training-center/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as Payload;

      const nextCourses = payload.courses ?? [];
      const nextPaths = payload.learning_paths ?? [];
      const nextCerts = payload.certifications ?? [];

      setDataAsOf(payload.data_as_of ?? '');
      setActiveTab((payload.active_tab ?? activeTab) as TabKey);
      setCourses(nextCourses);
      setLearningPaths(nextPaths);
      setCertifications(nextCerts);
      setFilters(payload.filters ?? EMPTY_FILTERS);

      setSelectedCourseId((prev) => (prev && nextCourses.some((x) => x.course_id === prev) ? prev : (nextCourses[0]?.course_id ?? null)));
      setSelectedPathId((prev) => (prev && nextPaths.some((x) => x.path_id === prev) ? prev : (nextPaths[0]?.path_id ?? null)));
      setSelectedCertId((prev) => (prev && nextCerts.some((x) => x.certification_id === prev) ? prev : (nextCerts[0]?.certification_id ?? null)));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load training center');
      setCourses([]);
      setLearningPaths([]);
      setCertifications([]);
      setFilters(EMPTY_FILTERS);
      setSelectedCourseId(null);
      setSelectedPathId(null);
      setSelectedCertId(null);
    } finally {
      setLoading(false);
    }
  }, [activeTab, category, level, role, status, search]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setCategory('');
    setLevel('');
    setRole('');
    setStatus('');
    setSearch('');
  }, [activeTab]);

  const selectedCourse = useMemo(() => courses.find((x) => x.course_id === selectedCourseId) ?? null, [courses, selectedCourseId]);
  const selectedPath = useMemo(() => learningPaths.find((x) => x.path_id === selectedPathId) ?? null, [learningPaths, selectedPathId]);
  const selectedCert = useMemo(() => certifications.find((x) => x.certification_id === selectedCertId) ?? null, [certifications, selectedCertId]);

  const resetFilters = (): void => {
    setCategory('');
    setLevel('');
    setRole('');
    setStatus('');
    setSearch('');
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold tracking-wide">TRAINING CENTER</h1>
            {dataAsOf && <p className="mt-1 text-xs text-slate-400">Data as of {dataAsOf}</p>}
          </div>
          <button onClick={() => void load()} className="inline-flex items-center gap-2 rounded-lg border border-slate-500 bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-600">
            <RefreshCw className="h-4 w-4" />Refresh
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-1 shadow-sm inline-flex">
        <button className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeTab === 'courses' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`} onClick={() => setActiveTab('courses')}>Courses</button>
        <button className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeTab === 'learning_paths' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`} onClick={() => setActiveTab('learning_paths')}>Learning Paths</button>
        <button className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeTab === 'certifications' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`} onClick={() => setActiveTab('certifications')}>Certifications</button>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex flex-wrap items-center gap-3">
        <Filter className="h-4 w-4 text-slate-400 shrink-0" />
        {activeTab === 'courses' && (
          <>
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="">All Categories</option>{filters.categories.map((x) => <option key={x} value={x}>{x}</option>)}</select>
            <select value={level} onChange={(e) => setLevel(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="">All Levels</option>{filters.levels.map((x) => <option key={x} value={x}>{x}</option>)}</select>
          </>
        )}
        {activeTab !== 'courses' && (
          <select value={role} onChange={(e) => setRole(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="">All Roles</option>{filters.roles.map((x) => <option key={x} value={x}>{x}</option>)}</select>
        )}
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-lg text-sm"><option value="">All Statuses</option>{filters.statuses.map((x) => <option key={x} value={x}>{x}</option>)}</select>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search" className="px-3 py-2 border border-slate-300 rounded-lg text-sm min-w-[220px]" />
        <button onClick={resetFilters} className="px-3 py-2 rounded-lg text-sm font-medium border border-slate-300 bg-slate-50 text-slate-600 hover:bg-slate-100">Reset</button>
      </div>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Loading training center...</div>}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      {activeTab === 'courses' && (
        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
            <table className="w-full text-sm"><thead><tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100"><th className="px-3 py-2 font-semibold">Course Name</th><th className="px-3 py-2 font-semibold">Category</th><th className="px-3 py-2 font-semibold">Level</th><th className="px-3 py-2 font-semibold">Duration</th><th className="px-3 py-2 font-semibold">Owner</th><th className="px-3 py-2 font-semibold">Last Updated</th><th className="px-3 py-2 font-semibold">Status</th></tr></thead>
            <tbody>{courses.length ? courses.map((r) => <tr key={r.course_id} onClick={() => setSelectedCourseId(r.course_id)} className={`border-b border-slate-100 cursor-pointer ${selectedCourseId === r.course_id ? 'bg-indigo-50' : 'hover:bg-slate-50'}`}><td className="px-3 py-2 font-medium text-slate-800">{r.course_name}</td><td className="px-3 py-2">{r.category}</td><td className="px-3 py-2">{r.level}</td><td className="px-3 py-2">{r.duration}</td><td className="px-3 py-2">{r.owner}</td><td className="px-3 py-2">{r.last_updated}</td><td className="px-3 py-2">{r.status}</td></tr>) : <tr><td className="px-3 py-6 text-slate-500" colSpan={7}>No courses for current filters.</td></tr>}</tbody></table>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-2">
            {selectedCourse ? <><p className="text-sm font-semibold text-slate-800">{selectedCourse.course_name}</p><p className="text-sm text-slate-600">{selectedCourse.description || 'No description available.'}</p><p className="text-xs uppercase tracking-wide text-slate-500">Learning Objectives</p><ul className="text-sm text-slate-700 list-disc ml-4">{selectedCourse.learning_objectives?.map((x, i) => <li key={`${x}-${i}`}>{x}</li>)}</ul><p className="text-xs uppercase tracking-wide text-slate-500">Modules</p><ul className="text-sm text-slate-700 list-disc ml-4">{selectedCourse.modules?.map((x, i) => <li key={`${x}-${i}`}>{x}</li>)}</ul><p className="text-sm text-slate-700">Duration: {selectedCourse.duration}</p><p className="text-sm text-slate-700">Owner: {selectedCourse.owner}</p><p className="text-sm text-slate-700">Last Updated: {selectedCourse.last_updated}</p><p className="text-sm text-slate-700">Status: {selectedCourse.status}</p></> : <p className="text-sm text-slate-500">Select a course row to view details.</p>}
          </div>
        </div>
      )}

      {activeTab === 'learning_paths' && (
        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
            <table className="w-full text-sm"><thead><tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100"><th className="px-3 py-2 font-semibold">Path Name</th><th className="px-3 py-2 font-semibold">Role</th><th className="px-3 py-2 font-semibold">Courses Count</th><th className="px-3 py-2 font-semibold">Estimated Duration</th><th className="px-3 py-2 font-semibold">Completion Rate</th><th className="px-3 py-2 font-semibold">Status</th></tr></thead>
            <tbody>{learningPaths.length ? learningPaths.map((r) => <tr key={r.path_id} onClick={() => setSelectedPathId(r.path_id)} className={`border-b border-slate-100 cursor-pointer ${selectedPathId === r.path_id ? 'bg-indigo-50' : 'hover:bg-slate-50'}`}><td className="px-3 py-2 font-medium text-slate-800">{r.path_name}</td><td className="px-3 py-2">{r.role}</td><td className="px-3 py-2">{r.courses_count}</td><td className="px-3 py-2">{r.estimated_duration}</td><td className="px-3 py-2">{fmtPct(r.completion_rate)}</td><td className="px-3 py-2">{r.status}</td></tr>) : <tr><td className="px-3 py-6 text-slate-500" colSpan={6}>No learning paths for current filters.</td></tr>}</tbody></table>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-2">
            {selectedPath ? <><p className="text-sm font-semibold text-slate-800">{selectedPath.path_name}</p><p className="text-sm text-slate-600">{selectedPath.overview}</p><p className="text-xs uppercase tracking-wide text-slate-500">Required Courses</p><ul className="text-sm text-slate-700 list-disc ml-4">{selectedPath.required_courses?.map((x, i) => <li key={`${x}-${i}`}>{x}</li>)}</ul><p className="text-sm text-slate-700">Progress Tracking: {selectedPath.progress_tracking}</p><p className="text-sm text-slate-700">Completion %: {fmtPct(selectedPath.completion_percent)}</p></> : <p className="text-sm text-slate-500">Select a learning path row to view details.</p>}
          </div>
        </div>
      )}

      {activeTab === 'certifications' && (
        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
            <table className="w-full text-sm"><thead><tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100"><th className="px-3 py-2 font-semibold">Certification Name</th><th className="px-3 py-2 font-semibold">Role</th><th className="px-3 py-2 font-semibold">Requirements</th><th className="px-3 py-2 font-semibold">Validity Period</th><th className="px-3 py-2 font-semibold">Status</th></tr></thead>
            <tbody>{certifications.length ? certifications.map((r) => <tr key={r.certification_id} onClick={() => setSelectedCertId(r.certification_id)} className={`border-b border-slate-100 cursor-pointer ${selectedCertId === r.certification_id ? 'bg-indigo-50' : 'hover:bg-slate-50'}`}><td className="px-3 py-2 font-medium text-slate-800">{r.certification_name}</td><td className="px-3 py-2">{r.role}</td><td className="px-3 py-2">{r.requirements}</td><td className="px-3 py-2">{r.validity_period}</td><td className="px-3 py-2">{r.status}</td></tr>) : <tr><td className="px-3 py-6 text-slate-500" colSpan={5}>No certifications for current filters.</td></tr>}</tbody></table>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-2">
            {selectedCert ? <><p className="text-sm font-semibold text-slate-800">{selectedCert.certification_name}</p><p className="text-sm text-slate-700">Requirements: {selectedCert.requirements}</p><p className="text-sm text-slate-700">Completion status: {selectedCert.completion_status}</p><p className="text-sm text-slate-700">Expiration tracking: {selectedCert.expiration_tracking}</p><p className="text-sm text-slate-700">Renewal requirements: {selectedCert.renewal_requirements}</p></> : <p className="text-sm text-slate-500">Select a certification row to view details.</p>}
          </div>
        </div>
      )}
    </div>
  );
};
