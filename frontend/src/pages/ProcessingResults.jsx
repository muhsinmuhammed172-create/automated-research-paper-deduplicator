import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart3, 
  Files, 
  Copy, 
  AlertTriangle, 
  Trash2, 
  CheckCircle2, 
  RefreshCw, 
  ArrowRight,
  UserCheck,
  FileText
} from 'lucide-react';

export default function ProcessingResults({ activeRunId }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    if (!activeRunId) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const res = await axios.get(`/api/runs/${activeRunId}/results`);
      setData(res.data);
    } catch (err) {
      console.error('Error fetching run results:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [activeRunId]);

  if (!activeRunId) {
    return (
      <div className="flex-1 p-10 flex items-center justify-center">
        <div className="bg-white border border-slate-200 rounded-xl p-8 text-center max-w-md shadow-xs">
          <Files className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-800">No Active Processing Run</h3>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            Upload PDFs from the Home page to start your first processing run.
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-bold shadow-xs hover:bg-blue-700"
          >
            Go to Upload Page
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 p-10 flex items-center justify-center">
        <div className="text-center text-slate-500 text-xs font-medium">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-2" />
          <span>Loading run results...</span>
        </div>
      </div>
    );
  }

  const metricCards = [
    {
      label: 'PDF files uploaded',
      value: data?.total_uploaded ?? 0,
      icon: Files,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'Exact file duplicates',
      value: data?.exact_file_duplicates ?? 0,
      icon: Copy,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      badge: 'SHA-256 match',
    },
    {
      label: 'Paper duplicate candidates',
      value: data?.paper_duplicate_candidates ?? 0,
      icon: AlertTriangle,
      color: 'text-rose-600',
      bg: 'bg-rose-50',
    },
    {
      label: 'Confirmed duplicate records',
      value: data?.confirmed_duplicates_removed ?? 0,
      icon: Trash2,
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
    {
      label: 'Unique retained records',
      value: data?.unique_retained_records ?? 0,
      icon: CheckCircle2,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      highlight: true,
    },
  ];

  return (
    <div className="flex-1 py-10 px-6 max-w-5xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider block">
            {activeRunId} Summary
          </span>
          <h2 className="text-xl font-bold text-slate-900 leading-tight">Deduplication Processing Results</h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/verification')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-xs"
          >
            <UserCheck className="w-4 h-4" />
            <span>Open Verification Queue</span>
            {data?.pending_verification > 0 && (
              <span className="ml-1 px-1.5 py-0.2 bg-white text-blue-700 rounded-full text-[10px] font-extrabold">
                {data.pending_verification}
              </span>
            )}
          </button>

          <button
            onClick={() => navigate('/prisma')}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-xs"
          >
            <FileText className="w-4 h-4" />
            <span>PRISMA Report</span>
          </button>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {metricCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className={`bg-white border rounded-xl p-5 shadow-xs flex flex-col justify-between ${
                card.highlight ? 'border-emerald-300 bg-emerald-50/20' : 'border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500">{card.label}</span>
                <div className={`p-2 rounded-lg ${card.bg}`}>
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900">{card.value}</div>
                {card.badge && (
                  <span className="text-[10px] font-bold text-amber-700 bg-amber-100/70 px-1.5 py-0.5 rounded w-fit mt-1 inline-block">
                    {card.badge}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Results Table & Stages */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Summary Metrics Table */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900">Run Metrics Breakdown</h3>
          <p className="text-xs text-slate-500">Calculated directly from the uploaded research paper collection</p>

          <table className="w-full text-xs text-left">
            <tbody className="divide-y divide-slate-100">
              <tr className="py-2.5">
                <td className="py-2.5 text-slate-600 font-medium">PDF files uploaded</td>
                <td className="py-2.5 text-right font-bold text-slate-900">{data?.total_uploaded}</td>
              </tr>
              <tr className="py-2.5">
                <td className="py-2.5 text-slate-600 font-medium">Exact file duplicates (SHA-256)</td>
                <td className="py-2.5 text-right font-bold text-amber-600">{data?.exact_file_duplicates}</td>
              </tr>
              <tr className="py-2.5">
                <td className="py-2.5 text-slate-600 font-medium">Paper duplicate candidates flagged</td>
                <td className="py-2.5 text-right font-bold text-rose-600">{data?.paper_duplicate_candidates}</td>
              </tr>
              <tr className="py-2.5">
                <td className="py-2.5 text-slate-600 font-medium">Candidates confirmed as duplicate</td>
                <td className="py-2.5 text-right font-bold text-red-600">{data?.confirmed_duplicates_removed}</td>
              </tr>
              <tr className="py-2.5">
                <td className="py-2.5 text-slate-600 font-medium">Candidates marked Not Duplicate</td>
                <td className="py-2.5 text-right font-bold text-blue-600">{data?.not_duplicate_retained}</td>
              </tr>
              <tr className="py-2.5">
                <td className="py-2.5 text-slate-600 font-medium">Candidates awaiting reviewer decision</td>
                <td className="py-2.5 text-right font-bold text-slate-700">{data?.pending_verification}</td>
              </tr>
              <tr className="py-3 bg-emerald-50/50 font-bold">
                <td className="py-3 px-2 text-emerald-900">Final unique research papers retained</td>
                <td className="py-3 px-2 text-right text-emerald-800 text-sm">{data?.unique_retained_records}</td>
              </tr>
            </tbody>
          </table>

          {data?.exact_file_duplicates > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs">
              <p className="font-bold text-amber-900 mb-1">Identified File Duplicates:</p>
              {data.file_duplicates_list.map((fd, idx) => (
                <div key={idx} className="text-amber-800 text-[11px]">
                  <strong>{fd.duplicate}</strong> is an exact binary duplicate of <strong>{fd.original}</strong> (matching SHA-256).
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Processing Stages Status */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900">Processing Stages Status</h3>
          <p className="text-xs text-slate-500">Execution state of each deduplication module</p>

          <div className="space-y-3 pt-1">
            {data?.stages.map((stg, i) => (
              <div key={i} className="flex items-center justify-between text-xs pb-2 border-b border-slate-100 last:border-0">
                <span className="font-medium text-slate-700">{stg.name}</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                  stg.status.includes('Completed') || stg.status.includes('Generated') || stg.status.includes('Reviewed')
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {stg.status}
                </span>
              </div>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-100">
            <button
              onClick={() => navigate('/verification')}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 shadow-2xs"
            >
              <span>Verify Candidates in Review Queue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
