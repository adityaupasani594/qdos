import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PlotlyPlot from 'react-plotly.js';
const Plot: any = (PlotlyPlot as any).default || PlotlyPlot;
import { Shield, Target, Activity, Settings2, Sliders, Activity as ActivityIcon } from 'lucide-react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

const API_URL = "http://localhost:8000";

function App() {
  const [patientData, setPatientData] = useState({
    age: 55,
    bsa: 1.8,
    days: 14,
    selected_drugs: ["Pembrolizumab", "Cisplatin"],
    efficacy: {
      Pembrolizumab: 5.0,
      Cisplatin: 6.0
    },
    toxicity: {
       Pembrolizumab: 2.0,
       Cisplatin: 4.0
    },
    toxicity_budget: 50.0,
    alpha: 1.0,
    beta: 1.0,
    gamma: 100.0,
    clearance_rate: 0.3,
    qaoa_reps: 1
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const availableDrugOptions = ["Pembrolizumab", "Cisplatin", "Paclitaxel", "Fluorouracil", "Doxorubicin"];

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.post(`${API_URL}/simulate`, patientData);
      if (resp.data.error) {
         setError(resp.data.error);
         setResults(null);
      } else {
        setResults(resp.data);
      }
    } catch (e: any) {
      setError(e.message || "Simulation Failed. Is the backend running?");
      setResults(null);
    }
    setLoading(false);
  };

  const handleDrugToggle = (drug: string) => {
    const newDrugs = patientData.selected_drugs.includes(drug)
      ? patientData.selected_drugs.filter(d => d !== drug)
      : [...patientData.selected_drugs, drug];
    
    const newEfficacy = { ...patientData.efficacy };
    const newToxicity = { ...patientData.toxicity };

    if (!newEfficacy[drug]) newEfficacy[drug] = 5.0;
    if (!newToxicity[drug]) newToxicity[drug] = 2.0;

    setPatientData({
      ...patientData,
      selected_drugs: newDrugs,
      efficacy: newEfficacy,
      toxicity: newToxicity
    });
  };

  return (
    <div className="min-h-screen bg-[#E6EEF5] text-slate-700 font-sans p-4 md:p-8">
      <div className="max-w-[1400px] mx-auto flex flex-col xl:flex-row gap-8">
        
        {/* Sidebar */}
        <div className="w-full xl:w-[400px] shrink-0 bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-8 h-fit border border-white/60">
          <div className="flex items-center gap-4 mb-8 pb-6 border-b border-slate-300/40">
            <div className="p-3 bg-indigo-500 text-white rounded-2xl shadow-[inset_2px_2px_4px_#3730a3,inset_-2px_-2px_4px_#818cf8]">
               <ActivityIcon size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-slate-800">Q-DOS</h1>
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Quantum Solver</p>
            </div>
          </div>

          <div className="space-y-8">
            <div className="space-y-4">
              <h3 className="flex items-center gap-2 font-black text-slate-700 uppercase text-xs tracking-widest bg-[#E6EEF5] shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-xl w-fit">
                <Target size={14} className="text-indigo-500" /> Patient Data
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Age (Yrs)" type="number" value={patientData.age} onChange={(v:any) => setPatientData({...patientData, age: Number(v)})} />
                <Input label="BSA (m²)" type="number" step="0.1" value={patientData.bsa} onChange={(v:any) => setPatientData({...patientData, bsa: Number(v)})} />
                <Input label="Horizon (Days)" type="number" className="col-span-2" value={patientData.days} onChange={(v:any) => setPatientData({...patientData, days: Number(v)})} />
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="flex items-center gap-2 font-black text-slate-700 uppercase text-xs tracking-widest bg-[#E6EEF5] shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-xl w-fit">
                <Shield size={14} className="text-indigo-500" /> Drug Library
              </h3>
              <div className="flex flex-wrap gap-2">
                {availableDrugOptions.map(drug => (
                  <button
                    key={drug}
                    onClick={() => handleDrugToggle(drug)}
                    className={cn(
                      "px-4 py-2 text-xs font-bold rounded-xl transition-all",
                      patientData.selected_drugs.includes(drug)
                        ? "bg-indigo-500 text-white shadow-[inset_2px_2px_4px_#3730a3,inset_-2px_-2px_4px_#818cf8]"
                        : "bg-[#E6EEF5] text-slate-600 shadow-[4px_4px_8px_#c4cacf,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff]"
                    )}
                  >
                    {drug}
                  </button>
                ))}
              </div>

              {patientData.selected_drugs.map(drug => (
                 <div key={drug} className="p-4 rounded-2xl bg-[#E6EEF5] shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] mt-4 border border-white/30">
                   <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest mb-3">{drug} Params</p>
                   <div className="grid grid-cols-2 gap-4">
                     <Input label="Efficacy" type="number" step="0.1" value={patientData.efficacy[drug]} onChange={(v:any) => setPatientData({...patientData, efficacy: {...patientData.efficacy, [drug]: Number(v)}})} />
                     <Input label="Toxicity" type="number" step="0.1" value={patientData.toxicity[drug]} onChange={(v:any) => setPatientData({...patientData, toxicity: {...patientData.toxicity, [drug]: Number(v)}})} />
                   </div>
                 </div>
              ))}
            </div>

            <div className="space-y-5">
              <h3 className="flex items-center gap-2 font-black text-slate-700 uppercase text-xs tracking-widest bg-[#E6EEF5] shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-xl w-fit">
                <Sliders size={14} className="text-indigo-500" /> Constraints
              </h3>
              <Slider label="Toxicity Budget" min={10} max={100} value={patientData.toxicity_budget} onChange={(v:any) => setPatientData({...patientData, toxicity_budget: Number(v)})} />
              <Slider label="Efficacy Weight (α)" min={0.1} max={5} step={0.1} value={patientData.alpha} onChange={(v:any) => setPatientData({...patientData, alpha: Number(v)})} />
              <Slider label="Toxicity Weight (β)" min={0.1} max={5} step={0.1} value={patientData.beta} onChange={(v:any) => setPatientData({...patientData, beta: Number(v)})} />
              <Slider label="Exclusion Penalty (γ)" min={10} max={500} step={5} value={patientData.gamma} onChange={(v:any) => setPatientData({...patientData, gamma: Number(v)})} />
              <Slider label="Clearance Rate" min={0.05} max={1.0} step={0.05} value={patientData.clearance_rate} onChange={(v:any) => setPatientData({...patientData, clearance_rate: Number(v)})} />
            </div>

            <div className="pt-4">
              <button
                 onClick={handleSimulate}
                 disabled={loading || patientData.selected_drugs.length * patientData.days > 16}
                 className="w-full py-4 bg-indigo-500 text-white font-black rounded-2xl shadow-[6px_6px_12px_#c4cacf,-6px_-6px_12px_#ffffff] transition-all transform active:translate-y-1 active:shadow-[inset_4px_4px_8px_#3730a3,inset_-4px_-4px_8px_#818cf8] uppercase tracking-[0.15em] text-sm hover:bg-indigo-400 group flex justify-center items-center gap-3 disabled:opacity-50 disabled:active:translate-y-0"
              >
                {loading ? <ActivityIcon className="animate-spin" /> : <ActivityIcon className="group-hover:scale-110 transition-transform" /> }
                {loading ? "Computing..." : "Run Quantum Solver"}
              </button>
              {(patientData.selected_drugs.length * patientData.days > 16) && (
                <p className="text-red-500 text-xs font-bold text-center mt-4 bg-red-100/50 p-2 rounded-lg">Max 16 variables supported (Days × Drugs).</p>
              )}
            </div>
            
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col gap-8 min-w-0">
           {error && (
             <div className="p-6 bg-[#E6EEF5] text-red-600 rounded-3xl shadow-[inset_6px_6px_12px_#c4cacf,inset_-6px_-6px_12px_#ffffff] border border-red-200/50 font-bold flex items-center gap-3">
               <div className="p-2 bg-red-100 rounded-full"><Activity size={20}/></div>
               {error}
             </div>
           )}

           {!results && !error && !loading && (
             <div className="flex-1 flex flex-col items-center justify-center p-12 bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] border border-white/60 text-slate-400 min-h-[600px]">
                <div className="p-6 rounded-3xl shadow-[inset_6px_6px_12px_#c4cacf,inset_-6px_-6px_12px_#ffffff] mb-6">
                  <Settings2 size={64} className="text-indigo-400/50" />
                </div>
                <h2 className="text-2xl font-black text-slate-600 mb-2">Awaiting Parameters</h2>
                <p className="text-sm font-medium text-center max-w-sm leading-relaxed">Configure the patient profile and drug library to the left, then run the solver to generate a personalized multidrug regimen.</p>
             </div>
           )}

           {results && (
             <>
               <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                 <MetricBox label="Objective Score" value={results.solution.metrics.objective_score.toFixed(2)} />
                 <MetricBox label="Total Efficacy" value={results.solution.metrics.total_efficacy.toFixed(2)} />
                 <MetricBox label="Total Toxicity" value={results.solution.metrics.total_toxicity.toFixed(2)} />
               </div>

               <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-8 border border-white/60">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 shadow-inner">
                      <Target size={16} />
                    </div>
                    <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">Optimized Schedule</h3>
                  </div>
                  
                  <ScheduleGrid schedule={results.solution.schedule} days={patientData.days} />
               </div>
               
               <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                 <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-8 border border-white/60 overflow-hidden flex flex-col">
                   <div className="flex items-center gap-3 mb-6">
                      <div className="w-8 h-8 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 shadow-inner">
                        <ActivityIcon size={16} />
                      </div>
                      <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">Toxicity Limit</h3>
                   </div>
                   <div className="flex-1 w-full bg-[#E6EEF5] rounded-2xl shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] p-4 flex items-center justify-center overflow-hidden">
                     <Plot
                        data={[
                          {
                            x: Array.from({length: patientData.days}, (_, i) => i),
                            y: results.charts.tox_qdos,
                            type: 'scatter',
                            mode: 'lines+markers',
                            fill: 'tozeroy',
                            name: 'Cumulative Toxicity (Q-DOS)',
                            line: {color: '#ef4444', width: 2},
                            fillcolor: 'rgba(239, 68, 68, 0.2)'
                          },
                          {
                             x: [0, patientData.days - 1],
                             y: [patientData.toxicity_budget, patientData.toxicity_budget],
                             mode: 'lines',
                             name: 'Safety Threshold',
                             line: {color: '#dc2626', width: 2, dash: 'dot'}
                          }
                        ]}
                        layout={{
                          autosize: true,
                          margin: {l:40, r:20, t:20, b:40},
                          paper_bgcolor: 'rgba(0,0,0,0)',
                          plot_bgcolor: 'rgba(0,0,0,0)',
                          xaxis: {title: 'Days'},
                          yaxis: {title: 'Toxicity Index'},
                          showlegend: false
                        }}
                        useResizeHandler={true}
                        style={{width: '100%', height: '100%'}}
                     />
                   </div>
                 </div>

                 <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-8 border border-white/60 flex flex-col">
                   <div className="flex items-center gap-3 mb-6">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 shadow-inner">
                        <Shield size={16} />
                      </div>
                      <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">Tumor Size Reduction</h3>
                   </div>
                   <div className="flex-1 w-full bg-[#E6EEF5] rounded-2xl shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] p-4 flex justify-center items-center overflow-hidden">
                     <Plot
                        data={[
                          {
                            x: Array.from({length: patientData.days}, (_, i) => i),
                            y: results.charts.tumor_std,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Standard Care',
                            line: {color: '#94a3b8', width: 2, dash: 'dash'},
                            marker: {symbol: 'circle', size: 6}
                          },
                          {
                            x: Array.from({length: patientData.days}, (_, i) => i),
                            y: results.charts.tumor_qdos,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Q-DOS Optimized',
                            line: {color: '#10b981', width: 3},
                            marker: {symbol: 'diamond', size: 8}
                          }
                        ]}
                        layout={{
                          autosize: true,
                          margin: {l:40, r:20, t:20, b:40},
                          paper_bgcolor: 'rgba(0,0,0,0)',
                          plot_bgcolor: 'rgba(0,0,0,0)',
                          xaxis: {title: 'Days'},
                          yaxis: {title: 'Size (%)'},
                          legend: {orientation: 'h', y: 1.1, x: 0}
                        }}
                        useResizeHandler={true}
                        style={{width: '100%', height: '100%'}}
                     />
                   </div>
                 </div>
               </div>
             </>
           )}
        </div>

      </div>
    </div>
  );
}

// Subcomponents

function Input({ label, value, onChange, ...props }: any) {
  return (
    <div className={props.className}>
      <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest pl-2 mb-2">{label}</label>
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[#E6EEF5] rounded-xl px-4 py-3 text-sm shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] focus:outline-none focus:ring-2 focus:ring-indigo-400 font-bold text-slate-700 transition-all border-none"
      />
    </div>
  );
}

function Slider({ label, value, onChange, ...props }: any) {
  return (
    <div>
      <div className="flex justify-between items-center mb-2 px-2">
        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{label}</label>
        <span className="text-xs font-black text-indigo-500 bg-[#E6EEF5] px-2 py-1 rounded-md shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff]">{value}</span>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        {...props}
        className="w-full h-3 bg-[#E6EEF5] rounded-full appearance-none shadow-[inset_3px_3px_6px_#c4cacf,inset_-3px_-3px_6px_#ffffff] accent-indigo-500 cursor-pointer"
      />
    </div>
  );
}

function MetricBox({ label, value }: { label: string, value: string | number }) {
  return (
    <div className="bg-[#E6EEF5] rounded-[2rem] p-6 shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] border border-white/60 flex flex-col items-center justify-center text-center">
       <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">{label}</span>
       <span className="text-4xl font-black text-indigo-600 drop-shadow-sm">{value}</span>
    </div>
  );
}

function ScheduleGrid({ schedule, days }: { schedule: any, days: number }) {
   if (!schedule) return null;
   
   const numDays = days;
   const daysArr = Array.from({length: numDays}, (_, i) => i);

   return (
     <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-4">
        {daysArr.map(day => {
           const drugsOnDay = Object.keys(schedule).filter(drug => schedule[drug][day] === 1);
           const isRest = drugsOnDay.length === 0;

           return (
             <div key={day} className={cn(
               "h-28 rounded-2xl flex flex-col items-center justify-center p-3 text-center transition-all border border-white/40",
               isRest ? "bg-[#E6EEF5] shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] text-slate-400"
                      : "bg-indigo-50 shadow-[6px_6px_12px_#c4cacf,-6px_-6px_12px_#ffffff] text-indigo-700 relative overflow-hidden"
             )}>
                {!isRest && <div className="absolute inset-0 bg-indigo-500/5 backdrop-blur-sm" />}
                <span className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-2 relative z-10">Day {day+1}</span>
                <span className="text-xs font-bold leading-tight relative z-10 drop-shadow-sm">
                  {isRest ? "Rest" : drugsOnDay.join(" + ")}
                </span>
             </div>
           )
        })}
     </div>
   )
}

function Gauge({ value, max, label }: { value: number, max: number, label: string }) {
   const ratio = Math.min(value / max, 1) * 100;
   return (
     <div className="flex flex-col items-center w-full">
       <div className="w-full bg-[#E6EEF5] rounded-full h-4 shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] overflow-hidden mb-4">
         <div className={cn("h-full transition-all duration-1000", ratio > 80 ? "bg-red-500" : "bg-emerald-400")} style={{ width: `${ratio}%`}} />
       </div>
       <div className="flex justify-between w-full text-[10px] font-black text-slate-500 uppercase tracking-widest">
         <span>0</span>
         <span>{value.toFixed(1)} / {max}</span>
       </div>
     </div>
   )
}

export default App;