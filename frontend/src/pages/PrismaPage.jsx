import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  FileText, 
  Download, 
  CheckCircle2, 
  RefreshCw, 
  Table, 
  Image as ImageIcon,
  Check,
  AlertCircle
} from 'lucide-react';

export default function PrismaPage({ activeRunId }) {
  const [data, setData] = useState({ metrics: [], total_retained: 0, retained_records: [], flowchart_available: false });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('flowchart');
  const [searchRetained, setSearchRetained] = useState('');

  const fetchPrisma = async () => {
    if (!activeRunId) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const res = await axios.get(`/api/runs/${activeRunId}/prisma`);
      setData(res.data);
    } catch (err) {
      console.error('Error fetching PRISMA data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrisma();
  }, [activeRunId]);

  if (!activeRunId) {
    return (
      <div className="flex-1 p-10 flex items-center justify-center">
        <p className="text-xs text-slate-500">Please select or upload a run first.</p>
      </div>
    );
  }

  // Filter retained records
  const filteredRetained = (data.retained_records || []).filter((r) => {
    const q = searchRetained.toLowerCase();
    return (
      r.title.toLowerCase().includes(q) ||
      r.author.toLowerCase().includes(q) ||
      r.doi.toLowerCase().includes(q) ||
      r.filename.toLowerCase().includes(q)
    );
  });

  // Calculate metrics for equation check
  const getMetricCount = (name) => {
    const row = (data.metrics || []).find((m) => m.metric.toLowerCase().includes(name.toLowerCase()));
    return row ? row.count : 0;
  };

  const initialCount = getMetricCount('identified in input');
  const confirmedRemoved = getMetricCount('removed as confirmed duplicates');
  const retainedCount = getMetricCount('remaining after deduplication') || data.total_retained;
  const equationValid = (initialCount - confirmedRemoved) === retainedCount;

  return (
    <div className="flex-1 py-10 px-6 max-w-5xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider block">
            {activeRunId} PRISMA Flowchart
          </span>
          <h2 className="text-xl font-bold text-slate-900 leading-tight">PRISMA Deduplication Flowchart & Report</h2>
          <p className="text-xs text-slate-500 mt-1">
            Automated PRISMA 2020 identification and deduplication workflow report.
          </p>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <a
            href={`/api/runs/${activeRunId}/download/retained-csv`}
            download
            className="px-3.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Retained CSV</span>
          </a>

          <a
            href={`/api/runs/${activeRunId}/download/summary-csv`}
            download
            className="px-3.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Summary CSV</span>
          </a>

          <a
            href={`/api/runs/${activeRunId}/download/flowchart-png`}
            download
            className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PNG</span>
          </a>

          <a
            href={`/api/runs/${activeRunId}/download/flowchart-pdf`}
            download
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </a>
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
          <span>PRISMA Flowchart & Mathematical Summary</span>
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
          <span>Unique Retained Papers ({data.total_retained})</span>
        </button>
      </div>

      {/* Tab 1: Flowchart & Math Summary */}
      {activeTab === 'flowchart' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left: PRISMA Diagram Viewer */}
          <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">PRISMA 2020 Flow Diagram</h3>
                <p className="text-xs text-slate-500">Rendered dynamically for {activeRunId}</p>
              </div>
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                Identification & Deduplication
              </span>
            </div>

            <div className="border border-slate-200 rounded-lg p-2 bg-slate-50/50 flex items-center justify-center min-h-[420px] overflow-hidden">
              {data.flowchart_available ? (
                <img
                  src={`/api/runs/${activeRunId}/flowchart.png?t=${Date.now()}`}
                  alt="PRISMA Flowchart"
                  className="max-w-full h-auto rounded shadow-2xs"
                />
              ) : (
                <div className="text-center p-8 text-slate-400">
                  <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <p className="text-xs">Flowchart being generated...</p>
                </div>
              )}
            </div>

            <p className="text-[11px] text-slate-400 italic leading-relaxed">
              * Note: The flowchart clearly separates exact SHA-256 file-level duplicates and paper-level candidates without double-counting.
            </p>
          </div>

          {/* Right: Mathematical Summary */}
          <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Mathematical Summary</h3>
            <p className="text-xs text-slate-500">Auditable deduplication accounting</p>

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

            {/* Validation Guard Box */}
            <div className="mt-4 p-4 rounded-xl bg-blue-50 border border-blue-200">
              <div className="flex items-center gap-2 mb-1.5 text-blue-900 font-bold text-xs">
                {equationValid ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span>Deduplication Equation Validated</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    <span>Pending Candidates Require Review</span>
                  </>
                )}
              </div>
              <p className="text-[11px] text-blue-800 leading-relaxed font-mono">
                Initial ({initialCount}) − Confirmed Removed ({confirmedRemoved}) = Final Retained ({retainedCount})
              </p>
              <p className="text-[10px] text-blue-600 mt-1">
                Zero double-counting between file-level and paper-level stages.
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
              <h3 className="text-sm font-bold text-slate-900">Unique Retained Research Papers</h3>
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
                  <th className="py-2.5 px-3">Filename</th>
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
                    <td className="py-2.5 px-3 font-semibold text-slate-900">{row.filename || '—'}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-800">{row.title}</td>
                    <td className="py-2.5 px-3 text-slate-600 truncate max-w-[180px]" title={row.author}>
                      {row.author || '—'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-blue-700 text-[11px]">
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
