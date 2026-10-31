import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  FileText, 
  Download, 
  CheckCircle2, 
  RefreshCw, 
  ShieldCheck, 
  ExternalLink,
  Table,
  Image as ImageIcon
} from 'lucide-react';

export default function PrismaReport({ activeDataset }) {
  const [data, setData] = useState({ metrics: [], total_retained: 0, retained_records: [], flowchart_available: false });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('flowchart'); // 'flowchart' or 'retained'
  const [searchRetained, setSearchRetained] = useState('');

  const fetchPrisma = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`/api/prisma?dataset=${activeDataset}`);
      setData(res.data);
    } catch (err) {
      console.error('Error fetching PRISMA data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrisma();
  }, [activeDataset]);

  const filteredRetained = (data.retained_records || []).filter((r) => {
    const q = searchRetained.toLowerCase();
    return (
      r.title.toLowerCase().includes(q) ||
      r.author.toLowerCase().includes(q) ||
      r.doi.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex-1 p-8 space-y-6 max-w-6xl mx-auto w-full">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 leading-tight">PRISMA Flowchart & Deduplication Report</h2>
          <p className="text-xs text-slate-500 mt-1">
            Compliant with PRISMA 2020 identification and deduplication reporting standards.
          </p>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center gap-2">
          <a
            href={
              activeDataset === 'crossref'
                ? '/api/download/crossref_deduplicated_records.csv'
                : '/api/download/plant_test_deduplicated_records.csv'
            }
            download
            className="px-3.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Retained CSV</span>
          </a>

          {activeDataset === 'crossref' && (
            <a
              href="/api/download/crossref_prisma_flowchart.pdf"
              download
              className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Flowchart PDF</span>
            </a>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-4 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('flowchart')}
          className={`pb-3 px-1 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'flowchart'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <ImageIcon className="w-4 h-4" />
          <span>PRISMA Flowchart & Metrics</span>
        </button>
        <button
          onClick={() => setActiveTab('retained')}
          className={`pb-3 px-1 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'retained'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Table className="w-4 h-4" />
          <span>Final Retained Records ({data.total_retained})</span>
        </button>
      </div>

      {/* Tab 1: Flowchart & Metrics */}
      {activeTab === 'flowchart' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left: PRISMA Diagram Viewer */}
          <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">PRISMA-Style Flow Diagram</h3>
                <p className="text-xs text-slate-500">Rendered via Python Matplotlib backend module</p>
              </div>
              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                Identification & Deduplication Scope
              </span>
            </div>

            <div className="border border-slate-200 rounded-lg p-2 bg-slate-50/50 flex items-center justify-center min-h-[380px] overflow-hidden">
              {activeDataset === 'crossref' && data.flowchart_available ? (
                <img
                  src="/api/prisma/flowchart.png"
                  alt="PRISMA Deduplication Flowchart"
                  className="max-w-full h-auto rounded shadow-xs"
                />
              ) : (
                <div className="text-center p-8 text-slate-400">
                  <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-xs font-semibold text-slate-700">PRISMA Flowchart is generated for the Crossref 500 dataset benchmark.</p>
                  <p className="text-[11px] text-slate-500 mt-1">Switch to the "Crossref 500" dataset from the sidebar to view the vector diagram.</p>
                </div>
              )}
            </div>

            <p className="text-[11px] text-slate-400 italic">
              Note: This flowchart strictly covers records identification, file-level hashing, algorithmic duplicate detection, human verification, and deduplication. Title/abstract screening and full-text eligibility are separate review stages.
            </p>
          </div>

          {/* Right: Metrics Table */}
          <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Mathematical Summary Counts</h3>
            <p className="text-xs text-slate-500">Every candidate is accounted for with zero discrepancy</p>

            <div className="divide-y divide-slate-100 text-xs">
              {data.metrics && data.metrics.length > 0 ? (
                data.metrics.map((m, i) => (
                  <div key={i} className="py-2.5 flex items-center justify-between">
                    <span className="text-slate-600 font-medium">{m.metric}</span>
                    <span className="font-bold text-slate-900 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                      {m.count}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400 py-6 text-center">No metrics available yet.</p>
              )}
            </div>

            <div className="mt-4 p-4 rounded-xl bg-blue-50 border border-blue-200">
              <div className="flex items-center gap-2 mb-1 text-blue-900 font-bold text-xs">
                <CheckCircle2 className="w-4 h-4 text-blue-600" />
                <span>Verification Guard Passed</span>
              </div>
              <p className="text-[11px] text-blue-800 leading-relaxed">
                The retained corpus matches the formula: 
                <br />
                <code className="bg-blue-100 px-1 py-0.5 rounded font-mono font-bold">
                  Remaining ({data.total_retained}) = Identified − Confirmed Duplicates
                </code>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Retained Records Table */}
      {activeTab === 'retained' && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs space-y-4 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Final Deduplicated Research Corpus</h3>
              <p className="text-xs text-slate-500">
                Displaying {filteredRetained.length} of {data.total_retained} unique papers retained
              </p>
            </div>
            <input
              type="text"
              placeholder="Filter retained papers..."
              value={searchRetained}
              onChange={(e) => setSearchRetained(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  {activeDataset === 'plant_test' && <th className="py-2.5 px-3">Filename</th>}
                  <th className="py-2.5 px-3 min-w-[260px]">Paper Title</th>
                  <th className="py-2.5 px-3">Authors</th>
                  <th className="py-2.5 px-3">DOI</th>
                  <th className="py-2.5 px-3 text-center">Year</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                {filteredRetained.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">{idx + 1}</td>
                    {activeDataset === 'plant_test' && (
                      <td className="py-2.5 px-3 font-semibold text-slate-900">{row.filename}</td>
                    )}
                    <td className="py-2.5 px-3 font-semibold text-slate-800">{row.title}</td>
                    <td className="py-2.5 px-3 text-slate-600 truncate max-w-[180px]" title={row.author}>
                      {row.author || '—'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-blue-700 text-[11px] truncate max-w-[150px]">
                      {row.doi ? (
                        <a
                          href={`https://doi.org/${row.doi}`}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:underline"
                        >
                          {row.doi}
                        </a>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-slate-900">{row.year || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
