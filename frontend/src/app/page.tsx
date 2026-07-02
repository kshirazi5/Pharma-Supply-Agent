"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { authFetch } from "@/lib/api";
import LoginForm from "@/components/LoginForm";
import UploadPanel from "@/components/UploadPanel";
import ApprovalsPanel from "@/components/ApprovalsPanel";
import DecisionsTable from "@/components/DecisionsTable";
import BudgetCard from "@/components/BudgetCard";

export default function Home() {
  const { token, logout } = useAuth();
  const [pipelineResult, setPipelineResult] = useState<string>("");
  const [budgetData, setBudgetData]         = useState({ budget: 50000, threshold: 10000 });
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const triggerRefresh = () => setRefreshTrigger(prev => prev + 1);

  const handlePipelineResult = (result: string) => {
    setPipelineResult(result);
    triggerRefresh();
  };

  useEffect(() => {
    if (!token) return;
    authFetch("/api/budget").then(setBudgetData).catch(() => {});
  }, [token]);

  if (!token) return <LoginForm />;

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800/60 sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-violet-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <div>
              <span className="font-bold text-slate-100 text-sm">Pharma Supply Intelligence</span>
              <span className="ml-2 text-slate-500 text-xs hidden sm:inline">v3.0 · Multi-Agent AI</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs px-3 py-1.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              API Online
            </div>
            <button
              id="logout-btn"
              onClick={logout}
              className="text-slate-400 hover:text-slate-200 text-xs transition px-3 py-1.5 rounded-lg hover:bg-slate-800"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Top row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Budget */}
          <BudgetCard budget={budgetData.budget} threshold={budgetData.threshold} />

          {/* Stats cards */}
          <div className="glass rounded-2xl p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <div className="text-slate-400 text-xs uppercase tracking-wider">Drug Categories</div>
              <div className="text-2xl font-bold text-violet-300">8 ATC</div>
              <div className="text-slate-500 text-xs mt-0.5">M01AB–R06</div>
            </div>
          </div>

          <div className="glass rounded-2xl p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div>
              <div className="text-slate-400 text-xs uppercase tracking-wider">Active Agents</div>
              <div className="text-2xl font-bold text-pink-300">5</div>
              <div className="text-slate-500 text-xs mt-0.5">Data·Forecast·Risk·Alert·Orchestrator</div>
            </div>
          </div>
        </div>

        {/* Middle row: Upload + Approvals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <UploadPanel token={token} onResult={handlePipelineResult} />
          <ApprovalsPanel token={token} refreshTrigger={refreshTrigger} onActionComplete={triggerRefresh} />
        </div>

        {/* Pipeline result */}
        {pipelineResult && (
          <div id="pipeline-result" className="glass rounded-2xl p-6 animate-fade-in">
            <h2 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Pipeline Result
            </h2>
            <pre className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed font-mono bg-slate-900/50 rounded-xl p-4 max-h-80 overflow-y-auto">
              {pipelineResult}
            </pre>
          </div>
        )}

        {/* Decisions table */}
        <DecisionsTable token={token} refreshTrigger={refreshTrigger} />

        {/* Agent Architecture */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">Agent Architecture</h2>
          <div className="flex flex-wrap items-center gap-3">
            {[
              { name: "Data Agent",       color: "from-sky-500 to-sky-600",     icon: "📂" },
              { name: "Forecast Agent",   color: "from-violet-500 to-violet-600", icon: "📈" },
              { name: "Risk Agent",       color: "from-amber-500 to-orange-600", icon: "⚠️" },
              { name: "Alert Agent",      color: "from-pink-500 to-rose-600",   icon: "🔔" },
              { name: "Orchestrator",     color: "from-emerald-500 to-teal-600", icon: "🎯" },
            ].map((agent, i) => (
              <div key={agent.name} className="flex items-center gap-2">
                <div className={`bg-gradient-to-r ${agent.color} rounded-xl px-4 py-2 text-white text-sm font-medium shadow-lg flex items-center gap-2`}>
                  <span>{agent.icon}</span>
                  {agent.name}
                </div>
                {i < 3 && <span className="text-slate-600 text-xl">→</span>}
                {i === 3 && <span className="text-slate-600 text-xl">→</span>}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
