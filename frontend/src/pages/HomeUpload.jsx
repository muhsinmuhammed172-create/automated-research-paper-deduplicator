import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  CheckCircle2, 
  Loader2, 
  Play, 
  FolderPlus,
  ArrowRight,
  Terminal,
  FileCheck
} from 'lucide-react';

export default function HomeUpload({ activeRunId, setActiveRunId }) {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [currentRunId, setCurrentRunId] = useState(null);
  const [runStatus, setRunStatus] = useState(null);

  const STEP_NAMES = [
    'PDF Ingestion & SHA-256 Hashes',
    'Crossref Metadata Enrichment',
    'File-Level Deduplication (SHA-256)',
    'Paper-Level Deduplication',
    'Preparing Verification Queue',
    'PRISMA Flowchart Generation'
  ];

  // Poll current run status if active
  useEffect(() => {
    if (!currentRunId) return;

    const pollStatus = async () => {
      try {
        const res = await axios.get(`/api/runs/${currentRunId}/status`);
        setRunStatus(res.data);
        if (res.data.status === 'completed') {
          setActiveRunId(currentRunId);
        }
      } catch (err) {
        console.error('Error polling run status:', err);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 1000);
    return () => clearInterval(interval);
  }, [currentRunId]);

  const handleFilesAdded = (newFileList) => {
    const valid = [];
    Array.from(newFileList).forEach((f) => {
      if (f.name.toLowerCase().endsWith('.pdf')) {
        if (!files.some((existing) => existing.name === f.name)) {
          valid.push(f);
        }
      }
    });
    setFiles((prev) => [...prev, ...valid]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    setFiles([]);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleStartProcessing = async () => {
    if (files.length === 0) return;

    try {
      setIsUploading(true);
      const formData = new FormData();
      files.forEach((f) => {
        formData.append('files', f);
      });

      const res = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const newRunId = res.data.run_id;
      setCurrentRunId(newRunId);
      setActiveRunId(newRunId);
      setRunStatus({
        run_id: newRunId,
        status: 'running',
        progress: 10,
        step: 'PDF Ingestion',
        message: 'Uploading and saving PDF files...',
        logs: [`[${new Date().toLocaleTimeString()}] Created ${newRunId}. Starting pipeline...`],
      });
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
      setIsUploading(false);
    }
  };

  const isRunning = runStatus && runStatus.status === 'running';
  const isCompleted = runStatus && runStatus.status === 'completed';

  return (
    <div className="flex-1 py-10 px-6 max-w-5xl mx-auto w-full space-y-8">
      {/* Hero Header */}
      <div className="text-center space-y-2 max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Research Paper Deduplication System
        </h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          Upload research papers to automatically extract metadata, identify duplicates and generate a PRISMA report.
        </p>
      </div>

      {/* Main Upload & Workflow Container */}
      {!isRunning && !isCompleted ? (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          {/* Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`p-10 text-center cursor-pointer border-b border-slate-200 transition-all ${
              dragOver
                ? 'bg-blue-50/70 border-blue-400'
                : 'hover:bg-slate-50/70 bg-slate-50/30'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={(e) => handleFilesAdded(e.target.files)}
            />
            <div className="w-14 h-14 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center mx-auto mb-4 shadow-sm shadow-blue-500/10">
              <UploadCloud className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-800">
              Drag and drop research-paper PDFs here
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              Select any collection of academic PDFs (e.g. P1–P7 test collection, or custom SLR literature).
            </p>
            <button
              type="button"
              className="mt-4 px-4 py-2 bg-white border border-slate-300 hover:border-slate-400 text-slate-700 text-xs font-bold rounded-lg shadow-2xs"
            >
              Browse Files
            </button>
          </div>

          {/* Selected File List */}
          <div className="p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-800">Selected Research Papers:</span>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                  {files.length} {files.length === 1 ? 'file' : 'files'}
                </span>
              </div>
              {files.length > 0 && (
                <button
                  type="button"
                  onClick={clearAll}
                  className="text-xs text-rose-600 hover:text-rose-700 font-semibold"
                >
                  Clear all
                </button>
              )}
            </div>

            {files.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No files selected yet. Drag PDFs into the box above or click Browse Files.
              </div>
            ) : (
              <div className="max-h-64 overflow-y-auto divide-y divide-slate-100 pr-1">
                {files.map((file, idx) => (
                  <div key={idx} className="py-2.5 flex items-center justify-between group">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <FileText className="w-4 h-4 text-blue-500 shrink-0" />
                      <div className="truncate">
                        <p className="text-xs font-semibold text-slate-800 truncate">{file.name}</p>
                        <p className="text-[10px] text-slate-400">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(idx)}
                      className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors"
                      title="Remove file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Main Action Button */}
            <div className="pt-6 border-t border-slate-100 mt-4">
              <button
                type="button"
                onClick={handleStartProcessing}
                disabled={files.length === 0 || isUploading}
                className={`w-full py-3 px-6 rounded-xl font-bold text-xs uppercase tracking-wider transition-all shadow-sm flex items-center justify-center gap-2 ${
                  files.length === 0 || isUploading
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/20'
                }`}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Initializing Run & Uploading...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>UPLOAD AND START DEDUPLICATION</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Progress & Stepper Display */
        <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider block">
                {runStatus?.run_id || 'Active Run'}
              </span>
              <h3 className="text-base font-bold text-slate-900">{runStatus?.name || 'Processing Pipeline'}</h3>
            </div>
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${
              isCompleted ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800 animate-pulse'
            }`}>
              {isCompleted ? 'Completed' : 'Running'}
            </span>
          </div>

          {/* Stepper */}
          <div className="space-y-4">
            {STEP_NAMES.map((name, idx) => {
              const currentStep = runStatus?.step || '';
              const progress = runStatus?.progress || 0;
              const stepThreshold = (idx + 1) * 16;
              const isPast = progress > stepThreshold || isCompleted;
              const isCurrent = !isCompleted && progress >= idx * 16 && progress <= stepThreshold;

              return (
                <div key={idx} className="flex items-center gap-3">
                  <div className="shrink-0">
                    {isPast ? (
                      <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                    ) : isCurrent ? (
                      <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center animate-pulse">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-xs font-semibold">
                        {idx + 1}
                      </div>
                    )}
                  </div>
                  <span className={`text-xs font-semibold ${
                    isPast ? 'text-emerald-700' : isCurrent ? 'text-blue-700 font-bold' : 'text-slate-400'
                  }`}>
                    {name}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Progress Bar */}
          <div className="space-y-2 pt-2">
            <div className="flex justify-between text-xs font-bold text-slate-700">
              <span>{runStatus?.message || 'Processing...'}</span>
              <span className="text-blue-600">{runStatus?.progress || 0}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${runStatus?.progress || 0}%` }}
              />
            </div>
          </div>

          {/* Real-time backend console log */}
          <div className="bg-slate-900 rounded-xl p-4 font-mono text-[11px] text-slate-300">
            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-800 text-slate-400 font-sans text-xs font-bold">
              <Terminal className="w-3.5 h-3.5" />
              <span>Pipeline Execution Log</span>
            </div>
            <div className="h-36 overflow-y-auto space-y-1">
              {runStatus?.logs && runStatus.logs.length > 0 ? (
                runStatus.logs.map((log, i) => (
                  <div key={i} className="text-emerald-400 font-mono">{log}</div>
                ))
              ) : (
                <p className="text-slate-500 italic">Executing backend algorithms...</p>
              )}
            </div>
          </div>

          {/* On completion actions */}
          {isCompleted && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h4 className="text-xs font-bold text-emerald-900">Pipeline Finished Successfully!</h4>
                <p className="text-xs text-emerald-700">All stages executed and metadata records are ready for review.</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/results')}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm"
                >
                  <span>View Processing Results</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
