import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  FileSpreadsheet, 
  UserCheck, 
  FileText, 
  Layers, 
  ShieldCheck,
  ExternalLink
} from 'lucide-react';

export default function Sidebar({ activeDataset, setActiveDataset }) {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/upload', label: 'Upload Papers', icon: UploadCloud },
    { to: '/metadata', label: 'Metadata & Enrichment', icon: FileSpreadsheet },
    { to: '/verification', label: 'Verification Queue', icon: UserCheck },
    { to: '/prisma', label: 'PRISMA Flowchart', icon: FileText },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col shrink-0 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white leading-tight">
              RESEARCH DEDUPLICATOR
            </h1>
            <p className="text-[11px] text-blue-300 font-medium">PRISMA Systematic Review</p>
          </div>
        </div>
      </div>

      {/* Dataset Context Switcher */}
      <div className="px-5 py-4 border-b border-slate-800/80 bg-slate-950/40">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
          Active Dataset
        </label>
        <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-800/90 rounded-lg text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveDataset('plant_test')}
            className={`py-1.5 px-2 rounded-md transition-all text-center ${
              activeDataset === 'plant_test'
                ? 'bg-blue-600 text-white shadow-sm font-semibold'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            P1–P7 PDFs
          </button>
          <button
            type="button"
            onClick={() => setActiveDataset('crossref')}
            className={`py-1.5 px-2 rounded-md transition-all text-center ${
              activeDataset === 'crossref'
                ? 'bg-blue-600 text-white shadow-sm font-semibold'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            Crossref 500
          </button>
        </div>
        <p className="text-[10px] text-slate-400 mt-2">
          {activeDataset === 'plant_test' 
            ? 'Ingestion, SHA-256 & Crossref for P1-P7'
            : 'Large-scale 500 records PRISMA benchmark'}
        </p>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-3 mb-2">
          Main Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-400">
        <div className="flex items-center gap-2 mb-2 text-slate-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-[11px] uppercase tracking-wide">PRISMA 2020 SLR Standard</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          MCA Final Project System. Human-in-the-loop duplicate verification.
        </p>
      </div>
    </aside>
  );
}
