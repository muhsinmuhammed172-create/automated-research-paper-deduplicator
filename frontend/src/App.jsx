import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomeUpload from './pages/HomeUpload';
import ProcessingResults from './pages/ProcessingResults';
import MetadataPage from './pages/MetadataPage';
import VerificationPage from './pages/VerificationPage';
import PrismaPage from './pages/PrismaPage';
import BenchmarkPage from './pages/BenchmarkPage';

export default function App() {
  const [activeRunId, setActiveRunId] = useState(() => {
    return localStorage.getItem('activeRunId') || null;
  });

  const handleSetActiveRun = (runId) => {
    setActiveRunId(runId);
    if (runId) {
      localStorage.setItem('activeRunId', runId);
    } else {
      localStorage.removeItem('activeRunId');
    }
  };

  return (
    <Router>
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900 antialiased">
        {/* Simplified Top Navigation Bar */}
        <Navbar activeRunId={activeRunId} setActiveRunId={handleSetActiveRun} />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col">
          <Routes>
            <Route
              path="/"
              element={<HomeUpload activeRunId={activeRunId} setActiveRunId={handleSetActiveRun} />}
            />
            <Route
              path="/results"
              element={<ProcessingResults activeRunId={activeRunId} />}
            />
            <Route
              path="/metadata"
              element={<MetadataPage activeRunId={activeRunId} />}
            />
            <Route
              path="/verification"
              element={<VerificationPage activeRunId={activeRunId} />}
            />
            <Route
              path="/prisma"
              element={<PrismaPage activeRunId={activeRunId} />}
            />
            <Route
              path="/benchmark"
              element={<BenchmarkPage />}
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
