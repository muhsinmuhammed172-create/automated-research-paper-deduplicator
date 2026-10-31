import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Layers, 
  UploadCloud, 
  BarChart3, 
  FileSpreadsheet, 
  UserCheck, 
  FileText, 
  Database,
  History,
  ChevronDown,
  CheckCircle2
} from 'lucide-react';

export default function Navbar({ activeRunId, setActiveRunId }) {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [showRunsDropdown, setShowRunsDropdown] = useState(false);

  const fetchRuns = async () => {
    try {
      const res = await axios.get('/api/runs');
      setRuns(res.data.runs || []);
      // If no active run selected and runs exist, default to the latest run
      if (!activeRunId && res.data.runs && res.data.runs.length > 0) {
        setActiveRunId(res.data.runs[0].run_id);
      }
    } catch (err) {
      console.error('Error fetching runs:', err);
    }
  };

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  const currentRun = runs.find((r) => r.run_id === activeRunId);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => navigate('/')} 
          className="flex items-center gap-3 cursor-pointer select-none"
        >
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-slate-900 leading-tight">
              RESEARCH DEDUPLICATOR
            </h1>
            <p className="text-[10px] text-blue-600 font-medium">PRISMA Systematic Review System</p>
          </div>
        </div>

        {/* 5 Main Navigation Links */}
        <nav className="hidden md:flex items-center gap-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`
            }
          >
            <UploadCloud className="w-4 h-4" />
            <span>1. Upload PDFs</span>
          </NavLink>

          <NavLink
            to="/results"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`
            }
          >
            <BarChart3 className="w-4 h-4" />
            <span>2. Processing Results</span>
          </NavLink>

          <NavLink
            to="/metadata"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`
            }
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>3. Metadata</span>
          </NavLink>

          <NavLink
            to="/verification"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`
            }
          >
            <UserCheck className="w-4 h-4" />
            <span>4. Duplicate Verification</span>
          </NavLink>

          <NavLink
            to="/prisma"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`
            }
          >
            <FileText className="w-4 h-4" />
            <span>5. PRISMA Report</span>
          </NavLink>
        </nav>

        {/* Right Actions: Run Selector & Benchmark */}
        <div className="flex items-center gap-3">
          {/* Run History Selector */}
          <div className="relative">
            <button
              onClick={() => setShowRunsDropdown(!showRunsDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition-colors"
            >
              <History className="w-3.5 h-3.5 text-blue-600" />
              <span>{currentRun ? currentRun.name || currentRun.run_id : 'No Run Active'}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {showRunsDropdown && (
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-lg border border-slate-200 py-2 z-50">
                <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 mb-1">
                  Processing Runs History
                </div>
                {runs.length === 0 ? (
                  <div className="px-4 py-3 text-xs text-slate-500 italic text-center">
                    No runs yet. Upload PDFs to start Run 001.
                  </div>
                ) : (
                  <div className="max-h-60 overflow-y-auto">
                    {runs.map((r) => (
                      <button
                        key={r.run_id}
                        onClick={() => {
                          setActiveRunId(r.run_id);
                          setShowRunsDropdown(false);
                          navigate('/results');
                        }}
                        className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-blue-50 transition-colors ${
                          activeRunId === r.run_id ? 'bg-blue-50/70 text-blue-700 font-bold' : 'text-slate-700'
                        }`}
                      >
                        <div className="truncate pr-2">
                          <p className="truncate">{r.name || r.run_id}</p>
                          <p className="text-[10px] text-slate-400 font-normal">{r.created_at || 'Recent'}</p>
                        </div>
                        {activeRunId === r.run_id && (
                          <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
                <div className="border-t border-slate-100 mt-1 pt-1 px-3">
                  <button
                    onClick={() => {
                      setShowRunsDropdown(false);
                      navigate('/');
                    }}
                    className="w-full text-center py-1.5 text-xs text-blue-600 font-bold hover:underline"
                  >
                    + Start New Run
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Separate Crossref 500 Benchmark Link */}
          <NavLink
            to="/benchmark"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                  : 'border-slate-200 bg-white text-slate-600 hover:text-indigo-600 hover:border-indigo-300'
              }`
            }
          >
            <Database className="w-3.5 h-3.5 text-indigo-500" />
            <span className="hidden sm:inline">Benchmark:</span>
            <span>Crossref 500</span>
          </NavLink>
        </div>
      </div>
    </header>
  );
}
