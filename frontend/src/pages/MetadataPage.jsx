import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Search, 
  Filter, 
  ExternalLink, 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle, 
  RefreshCw, 
  ChevronRight,
  ShieldAlert,
  Info
} from 'lucide-react';

export default function MetadataPage({ activeRunId }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedRecord, setSelectedRecord] = useState(null);

  const fetchMetadata = async () => {
    if (!activeRunId) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const params = {};
      if (searchQuery) params.q = searchQuery;
      if (statusFilter !== 'all') params.status = statusFilter;

      const res = await axios.get(`/api/runs/${activeRunId}/metadata`, { params });
      setRecords(res.data.records || []);
    } catch (err) {
      console.error('Error fetching run metadata:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetadata();
  }, [activeRunId, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchMetadata();
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    if (s.includes('title match')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3 h-3" />
          <span>Title Match</span>
        </span>
      );
    }
    if (s.includes('partial')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
          <Info className="w-3 h-3" />
          <span>Partial Match</span>
        </span>
      );
    }
    if (s.includes('needs review')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
          <AlertTriangle className="w-3 h-3" />
          <span>Needs Review</span>
        </span>
      );
    }
    if (s.includes('no doi')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-orange-50 text-orange-700 border border-orange-200">
          <AlertCircle className="w-3 h-3" />
          <span>No DOI</span>
        </span>
      );
    }
    if (s.includes('failed')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
          <ShieldAlert className="w-3 h-3" />
          <span>Lookup Failed</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700">
        {status || 'Unknown'}
      </span>
    );
  };

  return (
    <div className="flex-1 py-10 px-6 max-w-6xl mx-auto w-full space-y-6">
      {/* Header */}
      <div>
        <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider block">
          {activeRunId} Metadata
        </span>
        <h2 className="text-xl font-bold text-slate-900 leading-tight">Bibliographic Metadata Records</h2>
        <p className="text-xs text-slate-500 mt-1">
          Extracted PDF text metadata and Crossref REST API enriched fields. Click any record to inspect side-by-side comparison.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by title, author, DOI, or filename..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-600">Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg py-2 px-3 text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Validation Statuses</option>
            <option value="Title Match">Title Match</option>
            <option value="Needs Review">Needs Review</option>
            <option value="Lookup Failed">Lookup Failed</option>
            <option value="No DOI">No DOI</option>
          </select>
          <button
            onClick={fetchMetadata}
            className="p-2 border border-slate-200 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-50"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metadata Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Filename</th>
                <th className="py-3 px-4 min-w-[220px]">Paper Title</th>
                <th className="py-3 px-4 min-w-[150px]">Authors</th>
                <th className="py-3 px-4">DOI</th>
                <th className="py-3 px-4 text-center">Year</th>
                <th className="py-3 px-4">Journal</th>
                <th className="py-3 px-4">Publisher</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4 text-center">Validation Status</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
              {loading ? (
                <tr>
                  <td colSpan="10" className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-2" />
                    <span>Loading metadata...</span>
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan="10" className="py-12 text-center text-slate-400">
                    No metadata records found for this run.
                  </td>
                </tr>
              ) : (
                records.map((row, idx) => (
                  <tr
                    key={idx}
                    onClick={() => setSelectedRecord(row)}
                    className="hover:bg-blue-50/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-semibold text-slate-900 truncate max-w-[120px]" title={row.filename}>
                      {row.filename}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-800 line-clamp-2 max-w-[260px]" title={row.title}>
                      {row.title || <span className="text-slate-400 italic">None</span>}
                    </td>
                    <td className="py-3 px-4 truncate max-w-[160px]" title={row.author}>
                      {row.author || <span className="text-slate-400 italic">Not extracted</span>}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-blue-700 truncate max-w-[140px]" title={row.doi}>
                      {row.doi ? (
                        <a
                          href={`https://doi.org/${row.doi}`}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="hover:underline flex items-center gap-1"
                        >
                          <span>{row.doi}</span>
                          <ExternalLink className="w-2.5 h-2.5 shrink-0 opacity-70" />
                        </a>
                      ) : (
                        <span className="text-slate-400 italic">No DOI</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-900">{row.year || '—'}</td>
                    <td className="py-3 px-4 truncate max-w-[130px]" title={row.journal}>{row.journal || '—'}</td>
                    <td className="py-3 px-4 truncate max-w-[120px]" title={row.publisher}>{row.publisher || '—'}</td>
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap text-[11px]">{row.metadata_source}</td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">{getStatusBadge(row.validation_status)}</td>
                    <td className="py-3 px-4 text-right">
                      <button className="p-1 rounded text-slate-400 hover:text-blue-600 hover:bg-blue-100">
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-over Detailed Comparison Dialog */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-slate-900/40 backdrop-blur-xs">
          <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col overflow-y-auto animate-in slide-in-from-right duration-200">
            {/* Header */}
            <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50 sticky top-0 z-10">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600 block mb-0.5">
                  Detailed Metadata Inspection
                </span>
                <h3 className="text-base font-bold text-slate-900">{selectedRecord.filename}</h3>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Validation Summary */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-700">Enrichment Validation Status</span>
                  {getStatusBadge(selectedRecord.validation_status)}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-slate-500 font-medium">Title Match Score:</span>
                    <p className="font-bold text-slate-900">
                      {selectedRecord.title_match_score !== '' ? `${selectedRecord.title_match_score}` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500 font-medium">Metadata Source:</span>
                    <p className="font-bold text-slate-900">{selectedRecord.metadata_source}</p>
                  </div>
                </div>
                {selectedRecord.issue && (
                  <div className="p-2.5 rounded bg-amber-50 border border-amber-200 text-amber-800">
                    <strong>Validation Note:</strong> {selectedRecord.issue}
                  </div>
                )}
                {selectedRecord.file_hash && (
                  <div className="text-[11px] font-mono text-slate-500 truncate">
                    <span className="font-semibold text-slate-700 font-sans">SHA-256: </span>
                    {selectedRecord.file_hash}
                  </div>
                )}
              </div>

              {/* Side-by-side: PDF Extraction vs Crossref Retrieved */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Left: Original PDF */}
                <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
                  <div className="pb-2 border-b border-slate-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">Original PDF Extraction</span>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase">PyMuPDF</span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-slate-400 font-medium block">Extracted Title:</span>
                      <p className="font-semibold text-slate-800 mt-0.5 leading-snug">
                        {selectedRecord.pdf_title || <span className="text-slate-400 italic">None</span>}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium block">Extracted Authors:</span>
                      <p className="font-semibold text-slate-800 mt-0.5">
                        {selectedRecord.pdf_author || <span className="text-slate-400 italic">None</span>}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium block">Extracted DOI:</span>
                      <p className="font-mono text-blue-700 mt-0.5">
                        {selectedRecord.pdf_doi || <span className="text-slate-400 italic">None</span>}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium block">Extracted Year:</span>
                      <p className="font-semibold text-slate-800 mt-0.5">{selectedRecord.pdf_year || '—'}</p>
                    </div>
                  </div>
                </div>

                {/* Right: Crossref */}
                <div className="border border-blue-200 rounded-xl p-4 bg-blue-50/20 space-y-3">
                  <div className="pb-2 border-b border-blue-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-blue-900">Crossref REST API Record</span>
                    <span className="text-[10px] font-semibold text-blue-600 uppercase">Enriched</span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-slate-500 font-medium block">Full Paper Title:</span>
                      <p className="font-semibold text-slate-900 mt-0.5 leading-snug">
                        {selectedRecord.crossref_title || <span className="text-slate-400 italic">Not found</span>}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500 font-medium block">Standardized Authors:</span>
                      <p className="font-semibold text-slate-900 mt-0.5">
                        {selectedRecord.crossref_author || <span className="text-slate-400 italic">Not found</span>}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500 font-medium block">Crossref DOI:</span>
                      <p className="font-mono text-blue-700 mt-0.5">
                        {selectedRecord.crossref_doi || <span className="text-slate-400 italic">Not found</span>}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500 font-medium block">Publication Year:</span>
                      <p className="font-semibold text-slate-900 mt-0.5">{selectedRecord.crossref_year || '—'}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Publication Details */}
              <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-2 text-xs">
                <span className="font-bold text-slate-800 block pb-2 border-b border-slate-100">
                  Publication Details
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div>
                    <span className="text-slate-400 block font-medium">Journal:</span>
                    <p className="font-semibold text-slate-800 mt-0.5">{selectedRecord.journal || '—'}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Publisher:</span>
                    <p className="font-semibold text-slate-800 mt-0.5">{selectedRecord.publisher || '—'}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Publication Date:</span>
                    <p className="font-semibold text-slate-800 mt-0.5">{selectedRecord.publication_date || '—'}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Volume / Issue:</span>
                    <p className="font-semibold text-slate-800 mt-0.5">
                      {selectedRecord.volume ? `Vol. ${selectedRecord.volume}` : '—'} {selectedRecord.issue ? `(Iss. ${selectedRecord.issue})` : ''}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Pages:</span>
                    <p className="font-semibold text-slate-800 mt-0.5">{selectedRecord.page || '—'}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 mt-auto flex justify-end">
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
