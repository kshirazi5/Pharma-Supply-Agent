"use client";

import { useEffect, useState } from "react";
import { authFetch } from "@/lib/api";

const DRUG_COLS = ["M01AB","M01AE","N02BA","N02BE","N05B","N05C","R03","R06"];

interface Decision {
  id: number;
  created_at: string;
  drug_col: string;
  units_ordered: number;
  predicted_surge: boolean;
  confidence: number;
  anomaly_detected: boolean;
  status: string;
}

interface Props {
  token: string;
  refreshTrigger?: number;
}

const statusColor: Record<string, string> = {
  executed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  pending : "bg-amber-500/20 text-amber-400 border-amber-500/30",
  rejected: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function DecisionsTable({ token, refreshTrigger }: Props) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    authFetch("/api/decisions?limit=25")
      .then(d => setDecisions(d.decisions ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token, refreshTrigger]);

  if (loading) return (
    <div className="glass rounded-2xl p-6">
      <div className="text-slate-500 text-sm text-center py-8">Loading decisions…</div>
    </div>
  );

  return (
    <div className="glass rounded-2xl p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4">Recent Decisions</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 text-xs uppercase tracking-wider">
              <th className="pb-3 text-left">Date</th>
              <th className="pb-3 text-left">Drug</th>
              <th className="pb-3 text-right">Units</th>
              <th className="pb-3 text-right">Confidence</th>
              <th className="pb-3 text-center">Surge</th>
              <th className="pb-3 text-center">Anomaly</th>
              <th className="pb-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {decisions.map(d => (
              <tr key={d.id} id={`decision-row-${d.id}`} className="hover:bg-slate-800/30 transition">
                <td className="py-3 text-slate-400 text-xs">{new Date(d.created_at).toLocaleDateString()}</td>
                <td className="py-3 font-mono font-semibold text-sky-300">{d.drug_col}</td>
                <td className="py-3 text-right text-slate-200">{d.units_ordered.toFixed(0)}</td>
                <td className="py-3 text-right text-slate-300">{(d.confidence * 100).toFixed(1)}%</td>
                <td className="py-3 text-center">{d.predicted_surge ? "🔴" : "🟢"}</td>
                <td className="py-3 text-center">{d.anomaly_detected ? "⚠️" : "—"}</td>
                <td className="py-3 text-center">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium border ${statusColor[d.status] ?? ""}`}>
                    {d.status}
                  </span>
                </td>
              </tr>
            ))}
            {decisions.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">No decisions logged yet</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
