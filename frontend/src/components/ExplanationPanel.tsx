import React from 'react';
import { Sparkles, AlertTriangle, CheckCircle } from 'lucide-react';

interface ExplanationEntry {
  day: number;
  drugs: string[];
  rationale: string[];
}

interface ExplanationPanelProps {
  explanations: ExplanationEntry[];
}

const drugColors: Record<string, string> = {
  Pembrolizumab: 'bg-violet-100 text-violet-800 border-violet-300',
  Cisplatin:     'bg-blue-100 text-blue-800 border-blue-300',
  Paclitaxel:    'bg-emerald-100 text-emerald-800 border-emerald-300',
};

export default function ExplanationPanel({ explanations }: ExplanationPanelProps) {
  const activeDays = explanations.filter(e => e.drugs.length > 0);
  if (!activeDays.length) return null;

  return (
    <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff]
                    rounded-[2rem] p-6 border border-white/60">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center text-violet-600 shadow-inner">
          <Sparkles size={16} />
        </div>
        <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">
          Explainable Recommendations
        </h3>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
        {activeDays.map((entry) => (
          <div
            key={entry.day}
            className="bg-[#E6EEF5] rounded-2xl p-4 shadow-[inset_3px_3px_6px_#c4cacf,inset_-3px_-3px_6px_#ffffff]"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">
                Day {entry.day}
              </span>
              <div className="flex gap-1 flex-wrap">
                {entry.drugs.map(drug => (
                  <span
                    key={drug}
                    className={`text-[9px] font-black px-2 py-0.5 rounded-full border
                                ${drugColors[drug] ?? 'bg-slate-100 text-slate-700 border-slate-300'}`}
                  >
                    {drug}
                  </span>
                ))}
              </div>
            </div>
            <div className="space-y-1">
              {entry.rationale.map((r, i) => {
                const isWarn = r.startsWith('⚠');
                return (
                  <div key={i} className="flex items-start gap-2">
                    {isWarn
                      ? <AlertTriangle size={13} className="text-amber-500 mt-0.5 shrink-0" />
                      : <CheckCircle  size={13} className="text-emerald-500 mt-0.5 shrink-0" />
                    }
                    <p className={`text-[10px] leading-relaxed font-medium
                                   ${isWarn ? 'text-amber-700' : 'text-slate-600'}`}>
                      {r.replace('⚠ ', '')}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
