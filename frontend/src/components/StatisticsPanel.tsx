import React from 'react';
import PlotlyPlot from 'react-plotly.js';
const Plot: any = (PlotlyPlot as any).default || PlotlyPlot;
import { TrendingDown } from 'lucide-react';

interface ScheduleStat {
  strategy:             string;
  mean_tumor_reduction: number;
  ci_low:               number;
  ci_high:              number;
  mean_toxicity:        number;
  tox_ci_low:           number;
  tox_ci_high:          number;
}

interface StatisticsPanelProps {
  stats: ScheduleStat[];
}

const COLORS: Record<string, string> = {
  'Q-DOS':         '#4f46e5',
  'Standard Care': '#94a3b8',
  'Greedy':        '#f59e0b',
  'Random':        '#ef4444',
};

export default function StatisticsPanel({ stats }: StatisticsPanelProps) {
  if (!stats || !stats.length) return null;

  const strategies = stats.map(s => s.strategy);
  const means      = stats.map(s => s.mean_tumor_reduction);
  const errLow     = stats.map(s => s.mean_tumor_reduction - s.ci_low);
  const errHigh    = stats.map(s => s.ci_high - s.mean_tumor_reduction);
  const barColors  = strategies.map(s => COLORS[s] ?? '#64748b');

  return (
    <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff]
                    rounded-[2rem] p-6 border border-white/60">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center text-teal-600 shadow-inner">
          <TrendingDown size={16} />
        </div>
        <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">
          Monte Carlo Statistics — Tumor Reduction (%)
        </h3>
      </div>

      <div className="bg-[#E6EEF5] rounded-2xl shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] p-2 h-64">
        <Plot
          data={[
            {
              type:         'bar',
              x:            strategies,
              y:            means,
              error_y: {
                type:       'data',
                symmetric:  false,
                array:      errHigh,
                arrayminus: errLow,
                visible:    true,
                color:      '#334155',
                thickness:  2,
              },
              marker: { color: barColors },
              text:   means.map(m => `${m.toFixed(1)}%`),
              textposition: 'outside',
            },
          ]}
          layout={{
            autosize:     true,
            margin:       { l: 40, r: 20, t: 20, b: 60 },
            paper_bgcolor:'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            yaxis:        { title: 'Mean Reduction (%)', rangemode: 'tozero' },
            xaxis:        { tickangle: -15 },
            showlegend:   false,
          }}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      {/* Summary table */}
      <div className="mt-4 overflow-x-auto rounded-xl shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff]">
        <table className="w-full text-[9px]">
          <thead>
            <tr className="font-black text-slate-400 uppercase tracking-widest border-b border-slate-200/40">
              <th className="px-3 py-2 text-left">Strategy</th>
              <th className="px-3 py-2 text-center">Mean Red. %</th>
              <th className="px-3 py-2 text-center">95% CI</th>
              <th className="px-3 py-2 text-center">Mean Tox</th>
            </tr>
          </thead>
          <tbody>
            {stats.map(s => (
              <tr key={s.strategy}
                  className={`border-b border-slate-100/40 ${s.strategy === 'Q-DOS' ? 'bg-indigo-50/50 font-black' : ''}`}>
                <td className="px-3 py-2 font-bold text-slate-700">{s.strategy}</td>
                <td className="px-3 py-2 text-center text-slate-600">{s.mean_tumor_reduction.toFixed(1)}%</td>
                <td className="px-3 py-2 text-center text-slate-500">
                  [{s.ci_low.toFixed(1)}, {s.ci_high.toFixed(1)}]
                </td>
                <td className="px-3 py-2 text-center text-slate-600">{s.mean_toxicity.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
