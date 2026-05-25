import React from 'react';
import { BarChart2 } from 'lucide-react';

interface BaselineEntry {
  strategy: string;
  total_toxicity: number;
  total_efficacy: number;
}

interface MetricsEntry {
  total_toxicity: number;
  tumor_reduction_pct: number;
  budget: number;
  constraint_violated: boolean;
}

interface BaselineComparisonProps {
  qdosMetrics: MetricsEntry;
  baselines: {
    standard_care: BaselineEntry;
    greedy:        BaselineEntry;
    random:        BaselineEntry;
  };
}

const STRATEGY_COLORS: Record<string, string> = {
  'Q-DOS':         'text-indigo-600',
  'Standard Care': 'text-slate-500',
  'Greedy':        'text-amber-600',
  'Random':        'text-rose-500',
};

export default function BaselineComparison({ qdosMetrics, baselines }: BaselineComparisonProps) {
  const rows = [
    {
      strategy:        'Q-DOS',
      total_toxicity:  qdosMetrics.total_toxicity,
      tumor_reduction: qdosMetrics.tumor_reduction_pct,
      budget_safe:     !qdosMetrics.constraint_violated,
    },
    {
      strategy:        'Standard Care',
      total_toxicity:  baselines.standard_care.total_toxicity,
      tumor_reduction: null,
      budget_safe:     baselines.standard_care.total_toxicity <= qdosMetrics.budget,
    },
    {
      strategy:        'Greedy',
      total_toxicity:  baselines.greedy.total_toxicity,
      tumor_reduction: null,
      budget_safe:     baselines.greedy.total_toxicity <= qdosMetrics.budget,
    },
    {
      strategy:        'Random',
      total_toxicity:  baselines.random.total_toxicity,
      tumor_reduction: null,
      budget_safe:     baselines.random.total_toxicity <= qdosMetrics.budget,
    },
  ];

  return (
    <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff]
                    rounded-[2rem] p-6 border border-white/60">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 shadow-inner">
          <BarChart2 size={16} />
        </div>
        <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">
          Baseline Comparison
        </h3>
      </div>

      <div className="overflow-x-auto rounded-2xl shadow-[inset_3px_3px_6px_#c4cacf,inset_-3px_-3px_6px_#ffffff]">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[9px] font-black text-slate-400 uppercase tracking-widest border-b border-slate-200/50">
              <th className="px-4 py-3 text-left">Strategy</th>
              <th className="px-4 py-3 text-center">Total Toxicity</th>
              <th className="px-4 py-3 text-center">Tumor Reduction</th>
              <th className="px-4 py-3 text-center">Budget Safe?</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.strategy}
                className={`border-b border-slate-100/50 transition-colors
                            ${row.strategy === 'Q-DOS' ? 'bg-indigo-50/60' : 'bg-transparent'}`}
              >
                <td className={`px-4 py-3 font-black ${STRATEGY_COLORS[row.strategy] ?? 'text-slate-600'}`}>
                  {row.strategy}
                  {row.strategy === 'Q-DOS' && (
                    <span className="ml-2 text-[8px] bg-indigo-500 text-white px-1.5 py-0.5 rounded-full">
                      BEST
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-center font-bold text-slate-600">
                  {row.total_toxicity.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-center font-bold text-slate-600">
                  {row.tumor_reduction != null ? `${row.tumor_reduction.toFixed(1)}%` : '—'}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`text-[9px] font-black px-2 py-0.5 rounded-full
                                    ${row.budget_safe
                                      ? 'bg-emerald-100 text-emerald-700'
                                      : 'bg-rose-100 text-rose-700'}`}>
                    {row.budget_safe ? '✓ SAFE' : '✗ OVER'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
