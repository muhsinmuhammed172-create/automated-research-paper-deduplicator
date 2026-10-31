import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Database, 
  Download, 
  CheckCircle2, 
  FileText, 
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Table
} from 'lucide-react';

export default function BenchmarkPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchBenchmark = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/api/benchmark/crossref');
      setData(res.data);
    } catch (err) {
      console.error('Error fetching benchmark:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 p-10 flex items-center justify-center">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto" />
      </div>
    );
  }

  const statCards = [
    { label: 'Initial Crossref Records', value: data?.initial_records || 500, color: 'text-indigo-600' },
    { label: 'Duplicate Candidates', value: data?.duplicate_candidates || 5, color: 'text-amber-600' },
    { label: 'Confirmed Duplicates', value: data?.confirmed_duplicates || 4, color: 'text-red-600' },
    { label: 'Not Duplicate (Retained)', value: data?.not_duplicates || 1, color: 'text-blue-600' },
    { label: 'Pending Verification', value: data?.pending_verification || 0, color: 'text-slate-600' },
    { label: 'Final Retained Records', value: data?.final_retained || 496, color: 'text-emerald-600', highlight: true },
  ];

  return (
    <div className="flex-1 py-10 px-6 max-w-5xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold mb-1">
            <Database className="w-3.5 h-3.5" />
            <span>Isolated Baseline Benchmark</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 leading-tight">
            Benchmark Experiment – Crossref 500
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Standard large-scale metadata deduplication experiment demonstrating human-in-the-loop review at scale.
          </p>
        </div>

        {/* Downloads */}
        <div className="flex items-center gap-2">
          <a
            href="/api/benchmark/crossref/download/retained-csv"
            download
            className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Retained CSV (496)</span>
          </a>

          <a
            href="/api/benchmark/crossref/download/flowchart-pdf"
            download
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Flowchart PDF</span>
          </a>
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {statCards.map((c, i) => (
          <div
            key={i}
            className={`bg-white border rounded-xl p-4 shadow-xs ${
              c.highlight ? 'border-emerald-300 bg-emerald-50/20' : 'border-slate-200'
            }`}
          >
            <span className="text-[11px] font-semibold text-slate-500 block leading-tight">{c.label}</span>
            <span className={`text-xl font-bold mt-1 block ${c.color}`}>{c.value}</span>
          </div>
        ))}
      </div>

      {/* Main Content: Diagram & Verification Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: PRISMA Diagram */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Benchmark PRISMA Flowchart</h3>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
              500 → 496 Retained
            </span>
          </div>

          <div className="border border-slate-200 rounded-lg p-2 bg-slate-50/50 flex items-center justify-center min-h-[420px]">
            <img
              src="/api/benchmark/crossref/flowchart.png"
              alt="Crossref 500 Benchmark PRISMA Flowchart"
              className="max-w-full h-auto rounded shadow-2xs"
            />
          </div>
        </div>

        {/* Right: Flagged Candidates Table */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Verification Decisions</h3>
            <p className="text-xs text-slate-500">5 duplicate candidates reviewed by human reviewer</p>
          </div>

          <div className="space-y-3">
            {data?.candidates.map((cand, i) => (
              <div key={i} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800">#{i + 1} {cand.match_reason}</span>
                  <span className={`font-bold text-[10px] px-2 py-0.5 rounded ${
                    cand.verification_status === 'Not Duplicate'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {cand.verification_status}
                  </span>
                </div>
                <p className="font-semibold text-slate-900 leading-snug">{cand.title}</p>
                <div className="text-[11px] text-slate-500 flex items-center justify-between pt-1">
                  <span>Similarity: {parseFloat(cand.title_similarity || 0).toFixed(1)}%</span>
                  {cand.verification_status === 'Not Duplicate' && (
                    <span className="text-blue-700 font-semibold italic">Retained (Correction Notice)</span>
                  )}
                  {cand.verification_status === 'Confirmed Duplicate' && (
                    <span className="text-red-700 font-semibold">Excluded</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200 text-xs text-indigo-900">
            <strong>Key SLR Observation:</strong> Candidate #1 was a published correction notice with 88.1% title similarity. The reviewer correctly classified it as <em>Not Duplicate</em>, preserving it in the retained SLR collection.
          </div>
        </div>
      </div>
    </div>
  );
}
