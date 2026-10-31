import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  UserCheck, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  ArrowRight, 
  FileCheck2, 
  RefreshCw,
  ExternalLink,
  ShieldCheck
} from 'lucide-react';

export default function Verification({ activeDataset }) {
  const [data, setData] = useState({ candidates: [], total: 0, pending_count: 0 });
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);
  const [finalizing, setFinalizing] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`/api/verification/queue?dataset=${activeDataset}`);
      setData(res.data);
    } catch (err) {
      console.error('Error fetching verification queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [activeDataset]);

  const handleDecision = async (recordId, decision) => {
    try {
      setProcessingId(recordId);
      await axios.post('/api/verification/decide', {
        dataset: activeDataset,
        record_id: recordId,
        decision: decision
      });

      // Update local state immediately
      setData((prev) => {
        const updated = prev.candidates.map((c) => {
          if (c.record_id === recordId) {
            return {
              ...c,
              verification_status: decision,
              reviewer_decision: decision
            };
          }
          return c;
        });
        const pending = updated.filter(
          (c) => !['Confirmed Duplicate', 'Not Duplicate'].includes(c.verification_status)
        ).length;
        return { ...prev, candidates: updated, pending_count: pending };
      });

      setMessage({ type: 'success', text: `Saved decision: "${decision}" for record ${recordId}` });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      console.error('Failed to save decision:', err);
      alert('Failed to save decision: ' + (err.response?.data?.detail || err.message));
    } finally {
      setProcessingId(null);
    }
  };

  const handleFinalize = async () => {
    if (data.pending_count > 0) {
      alert(`There are still ${data.pending_count} pending candidates. Please review all candidates before finalizing.`);
      return;
    }

    try {
      setFinalizing(true);
      const res = await axios.post(`/api/verification/finalize?dataset=${activeDataset}`);
      setMessage({ type: 'success', text: res.data.message });
      fetchQueue();
    } catch (err) {
      console.error('Failed to finalize:', err);
      alert('Finalization error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setFinalizing(false);
    }
  };

  return (
    <div className="flex-1 p-8 space-y-6 max-w-6xl mx-auto w-full">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 leading-tight">Human Verification Queue</h2>
          <p className="text-xs text-slate-500 mt-1">
            Review algorithmic duplicate candidates. No paper is automatically removed without human confirmation.
          </p>
        </div>

        <button
          onClick={handleFinalize}
          disabled={finalizing || data.pending_count > 0 || data.candidates.length === 0}
          className={`px-4 py-2 rounded-lg text-xs font-semibold shadow-xs flex items-center gap-2 transition-all ${
            data.pending_count > 0 || data.candidates.length === 0
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
          }`}
        >
          {finalizing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Finalizing Dataset...</span>
            </>
          ) : (
            <>
              <FileCheck2 className="w-4 h-4" />
              <span>Finalize Retained Dataset</span>
            </>
          )}
        </button>
      </div>

      {message && (
        <div className={`p-3 rounded-lg text-xs font-semibold ${
          message.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800'
        }`}>
          {message.text}
        </div>
      )}

      {/* Queue Stats Bar */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 block">Total Flagged Candidates</span>
          <span className="text-xl font-bold text-slate-900 mt-1 block">{data.total}</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 block">Pending Review</span>
          <span className={`text-xl font-bold mt-1 block ${data.pending_count > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
            {data.pending_count}
          </span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 block">Reviewed Decisions</span>
          <span className="text-xl font-bold text-slate-900 mt-1 block">
            {data.total - data.pending_count}
          </span>
        </div>
      </div>

      {/* Candidate Review Cards */}
      {loading ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-2" />
          <span>Loading verification queue...</span>
        </div>
      ) : data.candidates.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center max-w-xl mx-auto shadow-xs">
          <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">Verification Queue is Empty</h3>
          <p className="text-xs text-slate-500 mt-1">
            No duplicate candidates are currently queued for verification in the {activeDataset} dataset.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {data.candidates.map((cand, idx) => {
            const isConfirmed = cand.verification_status === 'Confirmed Duplicate';
            const isRejected = cand.verification_status === 'Not Duplicate';
            const isPending = !isConfirmed && !isRejected;

            return (
              <div
                key={cand.record_id || idx}
                className={`bg-white border rounded-xl overflow-hidden shadow-xs transition-shadow hover:shadow-md ${
                  isConfirmed 
                    ? 'border-red-200 bg-red-50/10' 
                    : isRejected 
                    ? 'border-blue-200 bg-blue-50/10' 
                    : 'border-slate-200'
                }`}
              >
                {/* Card Header: Match Reason & Status Badge */}
                <div className="px-6 py-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-slate-900">Queue Item #{idx + 1}</span>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-800">
                      Reason: {cand.match_reason}
                    </span>
                    {cand.title_similarity > 0 && (
                      <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Similarity: {parseFloat(cand.title_similarity).toFixed(1)}%
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {isConfirmed && (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-red-700 bg-red-100 px-2.5 py-0.5 rounded-full">
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Confirmed Duplicate (Will be removed)</span>
                      </span>
                    )}
                    {isRejected && (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 bg-blue-100 px-2.5 py-0.5 rounded-full">
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Not Duplicate (Retained)</span>
                      </span>
                    )}
                    {isPending && (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-amber-700 bg-amber-100 px-2.5 py-0.5 rounded-full">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Pending Decision</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Card Body: Side-by-Side Comparison of Candidate vs Matched Record */}
                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Left: Candidate Paper */}
                  <div className="space-y-2 border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-rose-600 block">
                      Candidate Paper (Flagged)
                    </span>
                    <h4 className="text-xs font-bold text-slate-900 leading-snug">{cand.title}</h4>
                    <div className="text-xs space-y-1 text-slate-600 pt-2">
                      <p><strong className="text-slate-800">Authors:</strong> {cand.author || '—'}</p>
                      <p><strong className="text-slate-800">DOI:</strong> <span className="font-mono text-blue-700">{cand.doi || '—'}</span></p>
                      <p><strong className="text-slate-800">Year:</strong> {cand.year || '—'}</p>
                      {cand.filename && <p><strong className="text-slate-800">File:</strong> {cand.filename}</p>}
                    </div>
                  </div>

                  {/* Right: Matched Reference Paper */}
                  <div className="space-y-2 border border-blue-200 rounded-lg p-4 bg-blue-50/30">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-blue-700 block">
                      Matched Reference Paper (Already In Corpus)
                    </span>
                    {cand.matched_record ? (
                      <>
                        <h4 className="text-xs font-bold text-slate-900 leading-snug">{cand.matched_record.title}</h4>
                        <div className="text-xs space-y-1 text-slate-600 pt-2">
                          <p><strong className="text-slate-800">Authors:</strong> {cand.matched_record.author || '—'}</p>
                          <p><strong className="text-slate-800">DOI:</strong> <span className="font-mono text-blue-700">{cand.matched_record.doi || '—'}</span></p>
                          <p><strong className="text-slate-800">Year:</strong> {cand.matched_record.year || '—'}</p>
                          {cand.matched_record.filename && <p><strong className="text-slate-800">File:</strong> {cand.matched_record.filename}</p>}
                        </div>
                      </>
                    ) : (
                      <p className="text-xs text-slate-400 italic">Matched paper record details unavailable.</p>
                    )}
                  </div>
                </div>

                {/* Card Actions */}
                <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">Record ID: {cand.record_id}</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDecision(cand.record_id, 'Confirmed Duplicate')}
                      disabled={processingId === cand.record_id}
                      className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Confirm Duplicate</span>
                    </button>
                    <button
                      onClick={() => handleDecision(cand.record_id, 'Not Duplicate')}
                      disabled={processingId === cand.record_id}
                      className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Not Duplicate</span>
                    </button>
                    <button
                      onClick={() => handleDecision(cand.record_id, 'Pending')}
                      disabled={processingId === cand.record_id}
                      className="px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-colors"
                    >
                      Leave Pending
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
