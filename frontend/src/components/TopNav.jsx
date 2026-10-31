import React from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, CheckCircle2, Database, Shield } from 'lucide-react';

export default function TopNav({ activeDataset, title, subtitle }) {
  const navigate = useNavigate();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between shrink-0 shadow-xs">
      <div>
        <h2 className="text-lg font-bold text-slate-800 leading-tight">{title}</h2>
        <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Dataset badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-medium text-slate-700">
          <Database className="w-3.5 h-3.5 text-blue-600" />
          <span>Active:</span>
          <span className="font-semibold text-slate-900">
            {activeDataset === 'plant_test' ? 'P1–P7 PDF Dataset' : 'Crossref 500 Metadata'}
          </span>
        </div>

        {/* Verification mode pill */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Human Verification Required</span>
        </div>

        {/* Quick Upload action button */}
        <button
          onClick={() => navigate('/upload')}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload PDFs</span>
        </button>
      </div>
    </header>
  );
}
