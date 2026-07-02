"use client";

import { useEffect, useState } from "react";
import { authFetch } from "@/lib/api";

interface Approval {
  id: number;
  drug_col: string;
  units_ordered: number;
  estimated_cost: number;
  status: string;
  created_at: string;
}

interface Props {
  token: string;
  refreshTrigger?: number;
  onActionComplete?: () => void;
}

export default function ApprovalsPanel({ token, refreshTrigger, onActionComplete }: Props) {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading]     = useState(true);
  const [actioning, setActioning] = useState<number | null>(null);

  const fetchApprovals = async () => {
    try {
      const data = await authFetch("/api/approvals");
      setApprovals(data.pending ?? []);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchApprovals(); }, [token, refreshTrigger]);

  const handleAction = async (id: number, action: "approve" | "reject") => {
    setActioning(id);
    try {
      await authFetch(`/api/approve/${id}`, {
        method: "POST",
        body: JSON.stringify({ action, reviewer_note: `${action}d via dashboard` }),
      });
      await fetchApprovals();
      if (onActionComplete) onActionComplete();
    } catch { /* ignore */ }
    finally { setActioning(null); }
  };

  return (
    <div className="glass rounded-2xl p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${approvals.length > 0 ? "bg-amber-400 animate-pulse" : "bg-slate-600"}`} />
        Pending Approvals
        {approvals.length > 0 && (
          <span className="ml-auto bg-amber-500/20 text-amber-400 text-xs font-bold px-2 py-1 rounded-full border border-amber-500/30">
            {approvals.length}
          </span>
        )}
      </h2>

      {loading ? (
        <div className="text-center py-8 text-slate-500 text-sm">Loading…</div>
      ) : approvals.length === 0 ? (
        <div className="text-center py-8 text-slate-500 text-sm">
          <svg className="w-10 h-10 mx-auto mb-2 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          No pending approvals
        </div>
      ) : (
        <div className="space-y-3">
          {approvals.map(a => (
            <div key={a.id} id={`approval-${a.id}`} className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 flex items-center justify-between gap-4 animate-fade-in">
              <div>
                <div className="font-semibold text-amber-300">{a.drug_col}</div>
                <div className="text-slate-400 text-xs mt-0.5">
                  {a.units_ordered.toFixed(0)} units · ${a.estimated_cost.toFixed(0)} · {new Date(a.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  id={`approve-btn-${a.id}`}
                  onClick={() => handleAction(a.id, "approve")}
                  disabled={actioning === a.id}
                  className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 text-xs font-semibold px-3 py-1.5 rounded-lg transition disabled:opacity-50"
                >
                  ✓ Approve
                </button>
                <button
                  id={`reject-btn-${a.id}`}
                  onClick={() => handleAction(a.id, "reject")}
                  disabled={actioning === a.id}
                  className="bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 text-xs font-semibold px-3 py-1.5 rounded-lg transition disabled:opacity-50"
                >
                  ✗ Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
