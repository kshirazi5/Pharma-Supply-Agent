"use client";

interface Props {
  budget: number;
  threshold: number;
}

export default function BudgetCard({ budget, threshold }: Props) {
  return (
    <div className="glass rounded-2xl p-5 glow-border">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl bg-sky-500/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <div className="text-slate-400 text-xs uppercase tracking-wider">Procurement Budget</div>
          <div className="text-2xl font-bold text-sky-300">${budget.toLocaleString()}</div>
        </div>
      </div>
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Approval threshold</span>
        <span className="text-amber-400 font-medium">${threshold.toLocaleString()}</span>
      </div>
    </div>
  );
}
