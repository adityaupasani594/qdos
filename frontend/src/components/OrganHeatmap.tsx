import React from 'react';
import PlotlyPlot from 'react-plotly.js';
const Plot: any = (PlotlyPlot as any).default || PlotlyPlot;
import { Layers } from 'lucide-react';

interface OrganHeatmapProps {
  perOrganToxicity: Record<string, number[]>;
  days: number;
}

const ORGAN_LABELS: Record<string, string> = {
  kidney:   'Kidney',
  liver:    'Liver',
  marrow:   'Marrow',
  immune:   'Immune',
  vascular: 'Vascular',
};

export default function OrganHeatmap({ perOrganToxicity, days }: OrganHeatmapProps) {
  if (!perOrganToxicity) return null;

  const organs = Object.keys(perOrganToxicity).filter(k => ORGAN_LABELS[k]);
  const dayLabels = Array.from({ length: days }, (_, i) => `D${i + 1}`);

  const zData = organs.map(organ =>
    (perOrganToxicity[organ] ?? []).slice(0, days)
  );

  return (
    <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff]
                    rounded-[2rem] p-6 border border-white/60">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 shadow-inner">
          <Layers size={16} />
        </div>
        <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">
          Per-Organ Toxicity Heatmap
        </h3>
      </div>

      <div className="bg-[#E6EEF5] rounded-2xl shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] p-2 h-56">
        <Plot
          data={[
            {
              type:         'heatmap',
              z:            zData,
              x:            dayLabels,
              y:            organs.map(o => ORGAN_LABELS[o] ?? o),
              colorscale:   [[0, '#f0fdf4'], [0.5, '#fef3c7'], [1, '#fee2e2']],
              showscale:    true,
              hoverongaps:  false,
              hovertemplate:'<b>%{y}</b> — Day %{x}<br>Toxicity: %{z:.3f}<extra></extra>',
            },
          ]}
          layout={{
            autosize:     true,
            margin:       { l: 70, r: 10, t: 10, b: 40 },
            paper_bgcolor:'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis:        { title: 'Day' },
            yaxis:        { title: '' },
          }}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      <p className="text-[9px] text-slate-400 font-medium mt-3 text-center">
        Red = high toxicity accumulation for that organ on that day.
      </p>
    </div>
  );
}
