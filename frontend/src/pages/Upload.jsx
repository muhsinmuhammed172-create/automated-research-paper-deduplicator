import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Play, 
  FileCheck,
  Terminal,
  ArrowRight
} from 'lucide-react';

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [job, setJob] = useState({
    status: 'idle',
    step: '',
    progress: 0,
    message: '',
    logs: [],
    error: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const STEP_NAMES = [
    'Uploading PDFs',
    'Extracting Metadata',
    'Crossref Enrichment',
    'File Duplicate Detection',
    'Paper Duplicate Detection',
    'Preparing Verification Queue',
    'Completed'
  ];

  // Poll job status if a job is running
  useEffect(() => {
    let interval = null;
    const checkStatus = async () => {
      try {
        const res = await axios.get('/api/jobs/current');
        setJob(res.data);
      } catch (err) {
        console.error('Error polling job status:', err);
      }
    };

    checkStatus();

    if (job.status === 'running') {
      interval = setInterval(checkStatus, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [job.status]);

  const handleFileChange = (newFiles) => {
    const validPdfs = [];
    Array.from(newFiles).forEach((f) => {
      if (f.name.toLowerCase().endsWith('.pdf')) {
        // avoid duplicate selections in the local state
        if (!files.some((existing) => existing.name === f.name)) {
          validPdfs.push(f);
        }
      }
    });
    setFiles((prev) => [...prev, ...validPdfs]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    setFiles([]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files) {
      handleFileChange(e.dataTransfer.files);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleStartProcessing = async () => {
    if (files.length === 0) return;

    try {
      setIsSubmitting(true);
      const formData = new FormData();
      files.forEach((f) => {
        formData.append('files', f);
      });

      await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Update state to trigger polling
      setJob((prev) => ({
        ...prev,
        status: 'running',
        progress: 10,
        step: 'Uploading PDFs',
        message: 'Uploading PDF files to server...'
      }));
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 p-8 space-y-8 max-w-6xl mx-auto w-full">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 leading-tight">Upload Research Papers</h2>
        <p className="text-xs text-slate-500 mt-1">
          Upload PDF documents collected from academic databases (IEEE Xplore, Google Scholar, Scopus, Springer, Crossref).
        </p>
      </div>

      {/* Main Grid: Upload Area on Left, Processing Status on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Drag-and-drop & File List */}
        <div className="lg:col-span-7 space-y-6">
          {/* Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              dragOver
                ? 'border-blue-500 bg-blue-50/50 scale-[1.01]'
                : 'border-slate-300 hover:border-slate-400 bg-white'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={(e) => handleFileChange(e.target.files)}
            />
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4">
              <UploadCloud className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-800">
              Click to select or drag and drop PDF files
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Supports multiple PDF uploads (e.g. P1.pdf, P1_copy.pdf, P2.pdf ... P7.pdf)
            </p>
            <div className="mt-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-[11px] font-medium">
              <FileCheck className="w-3.5 h-3.5 text-blue-600" />
              <span>PDF format validated</span>
            </div>
          </div>

          {/* Uploaded File List */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-900">Queued PDFs</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                  {files.length} {files.length === 1 ? 'file' : 'files'}
                </span>
              </div>
              {files.length > 0 && (
                <button
                  type="button"
                  onClick={clearAll}
                  disabled={job.status === 'running'}
                  className="text-xs text-rose-600 hover:text-rose-700 font-medium"
                >
                  Clear all
                </button>
              )}
            </div>

            {files.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">
                No files selected yet. Choose files above or drag them into the upload zone.
              </p>
            ) : (
              <div className="max-h-60 overflow-y-auto divide-y divide-slate-100 pr-1">
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
                      disabled={job.status === 'running'}
                      onClick={() => removeFile(idx)}
                      className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors opacity-70 group-hover:opacity-100"
                      title="Remove file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Start Processing Action Button */}
            <div className="pt-4 border-t border-slate-100 mt-4">
              <button
                type="button"
                onClick={handleStartProcessing}
                disabled={files.length === 0 || job.status === 'running' || isSubmitting}
                className={`w-full py-2.5 px-4 rounded-lg font-semibold text-xs tracking-wide uppercase transition-all shadow-xs flex items-center justify-center gap-2 ${
                  files.length === 0 || job.status === 'running' || isSubmitting
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {job.status === 'running' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing In Progress...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>START PROCESSING</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Progress Stepper & Live Execution Log */}
        <div className="lg:col-span-5 space-y-6">
          {/* Stepper Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-1">Deduplication Workflow Stepper</h3>
            <p className="text-xs text-slate-500 mb-6">Real-time status of backend processing steps</p>

            <div className="space-y-4">
              {STEP_NAMES.map((stepName, index) => {
                const currentIdx = job.step_index || 0;
                const isCompleted = currentIdx > index + 1 || job.status === 'completed';
                const isCurrent = currentIdx === index + 1 && job.status === 'running';

                return (
                  <div key={index} className="flex items-center gap-3">
                    <div className="shrink-0">
                      {isCompleted ? (
                        <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-xs">
                          <CheckCircle2 className="w-4 h-4" />
                        </div>
                      ) : isCurrent ? (
                        <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center animate-pulse shadow-xs">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        </div>
                      ) : (
                        <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-400 border border-slate-200 flex items-center justify-center text-xs font-semibold">
                          {index + 1}
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p
                        className={`text-xs font-semibold truncate ${
                          isCompleted
                            ? 'text-emerald-700'
                            : isCurrent
                            ? 'text-blue-700 font-bold'
                            : 'text-slate-400'
                        }`}
                      >
                        {stepName}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Overall Progress Bar */}
            <div className="mt-6 pt-5 border-t border-slate-100">
              <div className="flex justify-between text-xs font-semibold mb-1.5">
                <span className="text-slate-600">Pipeline Progress</span>
                <span className="text-blue-600">{job.progress || 0}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${job.progress || 0}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500 font-medium mt-2">
                Status: <span className="font-semibold text-slate-800">{job.message || 'Waiting to start...'}</span>
              </p>
            </div>

            {/* Navigation button on complete */}
            {job.status === 'completed' && (
              <div className="mt-5 p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                <p className="text-xs font-bold text-emerald-800 mb-2">Processing finished successfully!</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate('/verification')}
                    className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center justify-center gap-1.5"
                  >
                    <span>Go to Verification</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => navigate('/metadata')}
                    className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded text-xs font-semibold flex items-center justify-center gap-1.5"
                  >
                    <span>View Metadata</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Real-time Backend Console Logs */}
          <div className="bg-slate-900 rounded-xl p-4 shadow-xs text-slate-300 font-mono text-[11px]">
            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-800 text-slate-400 font-sans text-xs font-bold">
              <Terminal className="w-3.5 h-3.5" />
              <span>Backend Execution Log</span>
            </div>
            <div className="h-44 overflow-y-auto space-y-1 pr-1">
              {job.logs && job.logs.length > 0 ? (
                job.logs.map((log, i) => (
                  <div key={i} className="text-emerald-400 leading-relaxed font-mono">
                    {log}
                  </div>
                ))
              ) : (
                <p className="text-slate-500 italic">No execution logs yet. Click START PROCESSING to run the pipeline.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
