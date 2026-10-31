import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  FileText, 
  Files, 
  Copy, 
  AlertTriangle, 
  Trash2, 
  CheckCircle, 
  TrendingUp, 
  Clock, 
  ArrowUpRight,
  RefreshCw,
  FolderOpen
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend 
} from 'recharts';

export default function Dashboard({ activeDataset }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await axios.get(`/api/stats?dataset=${activeDataset}`);
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
      setError('Failed to connect to backend server. Make sure Python FastAPI is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [activeDataset]);

  if (loading) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-3" />
          <p className="text-slate-600 font-medium text-sm">Loading research statistics from backend...</p>
        </div>
      </div>
    );
  }

  if (error || !stats || !stats.has_data) {
    return (
      <div className="flex-1 p-8">
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center max-w-2xl mx-auto shadow-xs">
          <FolderOpen className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-800 mb-2">No Processed Research Papers Found</h3>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            {error || 'No research paper records found for the current dataset. Please upload PDFs or run the deduplication pipeline.'}
          </p>
          <div className="flex justify-center gap-3">
            <button
              onClick={fetchStats}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry</span>
            </button>
            <a
              href="/upload"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-xs"
            >
              Upload Research Papers
            </a>
          </div>
        </div>
      </div>
    );
  }

  // Color palettes
  const STATUS_COLORS = {
    Distinct: '#10b981',           // Emerald
    Duplicate: '#ef4444',          // Red
    'Potential Duplicate': '#f59e0b', // Amber
  };

  const ENRICHMENT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#6366f1', '#ec4899'];

  const statCards = [
    {
      title: 'Total PDFs Uploaded',
      value: stats.total_pdfs,
      subtitle: 'In data/pdfs/ repository',
      icon: Files,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      title: 'Total Research Papers',
      value: stats.total_records,
      subtitle: 'Records identified in dataset',
      icon: FileText,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
    },
    {
      title: 'Exact File Duplicates',
      value: stats.exact_file_duplicates,
      subtitle: 'Matched via SHA-256 hash',
      icon: Copy,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      badge: 'SHA-256 Match',
    },
    {
      title: 'Paper Duplicate Candidates',
      value: stats.paper_duplicate_candidates,
      subtitle: 'Flagged by multi-rule algorithm',
      icon: AlertTriangle,
      color: 'text-rose-600',
      bg: 'bg-rose-50',
    },
    {
      title: 'Confirmed Duplicates Removed',
      value: stats.confirmed_duplicates_removed,
      subtitle: 'Verified by human reviewer',
      icon: Trash2,
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
    {
      title: 'Unique Papers Retained',
      value: stats.unique_papers_retained,
      subtitle: 'Final deduplicated PRISMA corpus',
      icon: CheckCircle,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      highlight: true,
    },
  ];

  return (
    <div className="flex-1 p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Top Statistic Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div 
              key={i} 
              className={`bg-white border rounded-xl p-5 shadow-xs transition-shadow hover:shadow-md flex flex-col justify-between ${
                card.highlight ? 'border-emerald-300 bg-emerald-50/20' : 'border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.title}</span>
                <div className={`p-2 rounded-lg ${card.bg}`}>
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 tracking-tight">{card.value}</div>
                <div className="text-[11px] text-slate-500 font-medium mt-1">{card.subtitle}</div>
              </div>
              {card.badge && (
                <div className="mt-2 text-[10px] font-bold text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded w-fit">
                  {card.badge}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Visual Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: File-Level vs Paper-Level Duplicate Comparison */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Duplicate Detection Level Comparison</h3>
              <p className="text-xs text-slate-500">File-level SHA-256 vs Paper-level algorithmic matches</p>
            </div>
            <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md">
              Two-Tier Detection
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.comparison_data} margin={{ top: 10, right: 20, left: -20, bottom: 20 }}>
                <XAxis dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} interval={0} angle={-5} textAnchor="end" />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', fontSize: '12px' }} 
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Duplicate Status Breakdown */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Duplicate Detection Status Distribution</h3>
              <p className="text-xs text-slate-500">Classification of the current dataset records</p>
            </div>
            <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md">
              Verification Required
            </span>
          </div>

          <div className="h-64 flex items-center justify-center">
            {stats.status_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.status_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {stats.status_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || '#94a3b8'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-400">No status distribution available yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: Metadata Enrichment Status & PRISMA Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Enrichment Status Breakdown */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs lg:col-span-1">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Metadata Enrichment Status</h3>
          <p className="text-xs text-slate-500 mb-6">Crossref bibliographic validation check</p>

          <div className="space-y-4">
            {stats.enrichment_distribution.length > 0 ? (
              stats.enrichment_distribution.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span 
                      className="w-2.5 h-2.5 rounded-full" 
                      style={{ backgroundColor: ENRICHMENT_COLORS[idx % ENRICHMENT_COLORS.length] }}
                    />
                    <span className="font-medium text-slate-700">{item.name}</span>
                  </div>
                  <span className="font-bold text-slate-900">{item.value} papers</span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-6 text-center">
                Metadata enrichment distribution data unavailable.
              </div>
            )}
          </div>
        </div>

        {/* PRISMA Deduplication Summary Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">PRISMA Deduplication Summary</h3>
              <p className="text-xs text-slate-500">Official mathematical consistency breakdown</p>
            </div>
            <a 
              href="/prisma"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>View Flowchart</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">PRISMA Flow Metric</th>
                  <th className="py-2.5 px-4 text-right">Count</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {stats.prisma_summary.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="py-2 px-4">{row.metric}</td>
                    <td className="py-2 px-4 text-right font-bold text-slate-900">{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Activity Log */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-500" />
          <span>Recent Processing Activity</span>
        </h3>
        <div className="space-y-3">
          {stats.recent_activity.map((act, i) => (
            <div key={i} className="flex items-start justify-between border-b border-slate-100 pb-3 last:border-0 last:pb-0">
              <div>
                <p className="text-xs font-semibold text-slate-800">{act.action}</p>
                <p className="text-xs text-slate-500 mt-0.5">{act.details}</p>
              </div>
              <span className="text-[11px] text-slate-400 bg-slate-50 px-2 py-1 rounded font-medium shrink-0">
                {act.time}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
