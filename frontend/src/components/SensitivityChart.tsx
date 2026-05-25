import React from 'react';
import PlotlyPlot from 'react-plotly.js';
const Plot: any = (PlotlyPlot as any).default || PlotlyPlot;
import { Gauge } from 'lucide-react';

interface ParameterSens {
  parameter:         string;
  values:            number[];
  objective_scores:  number[];
  sensitivity_index: number;
}

interface SensitivityChartProps {
  parameters: ParameterSens[];
  baselineScore: number;
}

const PARAM_LABELS: Record<string, string> = {
  age:      'Age',
  kidney:   'Kidney',
  liver:    'Liver',
  marrow:   'Marrow',
  immune:   'Immune',
  vascular: 'Vascular',
  PDL1:     'PD-L1',
  BRCA:     'BRCA',
  VEGF:     'VEGF',
};

export default function SensitivityChart({ parameters, baselineScore }: SensitivityChartProps) {
  if (!parameters || !parameters.length) return null;

  const sorted  = [...parameters].sort((a, b) => b.sensitivity_index - a.sensitivity_index);
  const names   = sorted.map(p => PARAM_LABELS[p.parameter] ?? p.parameter);
  const indices = sorted.map(p => p.sensitivity_index);
  const max_idx = Math.max(...indices, 0.001);
  const barColors = indices.map(v => v > max_idx * 0.5 ? '#4f46e5' : '#a5b4fc');

  return (
    <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff]
                    rounded-[2rem] p-6 border border-white/60">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-full bg-pink-100 flex items-center justify-center text-pink-600 shadow-inner">
          <Gauge size={16} />
        </div>
        <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">
          Sensitivity Analysis (Tornado)
        </h3>
      </div>

      <div className="bg-[#E6EEF5] rounded-2xl shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] p-2 h-72">
        <Plot
          data={[
            {
              type:        'bar',
              orientation: 'h',
              y:           names,
              x:           indices,
              marker:      { color: barColors },
              text:        indices.map(v => v.toFixed(3)),
              textposition:'outside',
              hovertemplate: '<b>%{y}</b><br>Sensitivity: %{x:.4f}<extra></extra>',
            },
          ]}
          layout={{
            autosize:     true,
            margin:       { l: 80, r: 50, t: 10, b: 40 },
            paper_bgcolor:'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis:        { title: 'Normalized |S_i|' },
            yaxis:        { autorange: 'reversed' },
            showlegend:   false,
          }}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      <p className="text-[9px] text-slate-400 font-medium mt-3 text-center">
        Higher bars → parameter has greater impact on optimizer objective.
        Baseline score: {baselineScore.toFixed(4)}
      </p>
    </div>
  );
}
