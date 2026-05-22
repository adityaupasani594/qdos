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
    age: 40,
    days: 14,
    selected_drugs: ["Pembrolizumab", "Cisplatin", "Paclitaxel"],
    patient_profile: {
      kidney: 1.0,
      liver: 1.0,
      marrow: 1.0,
      immune: 1.0,
      vascular: 1.0
    },
    subtype_scores: {
      BRCA: 0.5,
      PDL1: 0.5,
      VEGF: 0.5
    },
    mutually_exclusive_pairs: [["Cisplatin", "Paclitaxel"]],
    gap_constraints: {"Pembrolizumab": 1},
    max_drugs_per_day: 2,
    base_toxicity_budget: 10.0
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const availableDrugOptions = ["Pembrolizumab", "Cisplatin", "Paclitaxel", "Doxorubicin"];

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

    setPatientData({
      ...patientData,
      selected_drugs: newDrugs
    });
  };

  const handleProfileChange = (organ: string, value: string) => {
    setPatientData({
      ...patientData,
      patient_profile: {
        ...patientData.patient_profile,
        [organ]: Number(value)
      }
    });
  }
  
  const handleSubtypeChange = (pathway: string, value: string) => {
    setPatientData({
      ...patientData,
      subtype_scores: {
        ...patientData.subtype_scores,
        [pathway]: Number(value)
      }
    });
  }

  return (
    <div className="min-h-screen bg-[#E6EEF5] text-slate-700 font-sans p-4 md:p-8">
      <div className="max-w-[1400px] mx-auto flex flex-col xl:flex-row gap-8">
        
        {/* Sidebar */}
        <div className="w-full xl:w-[450px] shrink-0 bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-8 h-fit border border-white/60">
          <div className="flex items-center gap-4 mb-4 pb-4 border-b border-slate-300/40">
            <div className="p-3 bg-indigo-500 text-white rounded-2xl shadow-[inset_2px_2px_4px_#3730a3,inset_-2px_-2px_4px_#818cf8]">
               <ActivityIcon size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-slate-800">Q-DOS</h1>
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Quantum Solver</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 font-black text-slate-700 uppercase text-xs tracking-widest bg-[#E6EEF5] shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-xl w-fit">
                <Target size={14} className="text-indigo-500" /> Patient Params
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Age(Yrs)" type="number" value={patientData.age} onChange={(v:any) => setPatientData({...patientData, age: Number(v)})} />
                <Input label="Horizon" type="number" value={patientData.days} onChange={(v:any) => setPatientData({...patientData, days: Number(v)})} />
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="flex items-center gap-2 font-black text-slate-700 uppercase text-xs tracking-widest bg-[#E6EEF5] shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-xl w-fit">
                Organ Profile (0.1-1.0)
              </h3>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                 <Slider label="Kidney" min={0.1} max={1.0} step={0.1} value={patientData.patient_profile.kidney} onChange={(v:any) => handleProfileChange("kidney", v)} />
                 <Slider label="Liver" min={0.1} max={1.0} step={0.1} value={patientData.patient_profile.liver} onChange={(v:any) => handleProfileChange("liver", v)} />
                 <Slider label="Marrow" min={0.1} max={1.0} step={0.1} value={patientData.patient_profile.marrow} onChange={(v:any) => handleProfileChange("marrow", v)} />
                 <Slider label="Immune" min={0.1} max={1.0} step={0.1} value={patientData.patient_profile.immune} onChange={(v:any) => handleProfileChange("immune", v)} />
                 <Slider label="Vascular" min={0.1} max={1.0} step={0.1} value={patientData.patient_profile.vascular} onChange={(v:any) => handleProfileChange("vascular", v)} />
                 <Slider label="Budget" min={1.0} max={25.0} step={1.0} value={patientData.base_toxicity_budget} onChange={(v:any) => setPatientData({...patientData, base_toxicity_budget: Number(v)})} />
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="flex items-center gap-2 font-black text-slate-700 uppercase text-xs tracking-widest bg-[#E6EEF5] shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-xl w-fit">
                Tumor Subtype
              </h3>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                 <Slider label="BRCA" min={0.0} max={1.0} step={0.1} value={patientData.subtype_scores.BRCA} onChange={(v:any) => handleSubtypeChange("BRCA", v)} />
                 <Slider label="PDL1" min={0.0} max={1.0} step={0.1} value={patientData.subtype_scores.PDL1} onChange={(v:any) => handleSubtypeChange("PDL1", v)} />
                 <Slider label="VEGF" min={0.0} max={1.0} step={0.1} value={patientData.subtype_scores.VEGF} onChange={(v:any) => handleSubtypeChange("VEGF", v)} />
                 <Input label="Max Drugs/Day" type="number" value={patientData.max_drugs_per_day} onChange={(v:any) => setPatientData({...patientData, max_drugs_per_day: Number(v)})} />
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="flex items-center gap-2 font-black text-slate-700 uppercase text-xs tracking-widest bg-[#E6EEF5] shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-xl w-fit">
                <Shield size={14} className="text-indigo-500" /> Drug Library
              </h3>
              <div className="flex flex-wrap gap-2">
                {availableDrugOptions.map(drug => (
                  <button
                    key={drug}
                    onClick={() => handleDrugToggle(drug)}
                    className={cn(
                      "px-3 py-1.5 text-xs font-bold rounded-xl transition-all",
                      patientData.selected_drugs.includes(drug)
                        ? "bg-indigo-500 text-white shadow-[inset_2px_2px_4px_#3730a3,inset_-2px_-2px_4px_#818cf8]"
                        : "bg-[#E6EEF5] text-slate-600 shadow-[4px_4px_8px_#c4cacf,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff]"
                    )}
                  >
                    {drug}
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-2">
              <button
                 onClick={handleSimulate}
                 disabled={loading}
                 className="w-full py-4 bg-indigo-500 text-white font-black rounded-2xl shadow-[6px_6px_12px_#c4cacf,-6px_-6px_12px_#ffffff] transition-all transform active:translate-y-1 active:shadow-[inset_4px_4px_8px_#3730a3,inset_-4px_-4px_8px_#818cf8] uppercase tracking-[0.15em] text-sm hover:bg-indigo-400 flex justify-center items-center gap-3 disabled:opacity-50"
              >
                {loading ? <ActivityIcon className="animate-spin" /> : <ActivityIcon className="group-hover:scale-110 transition-transform" /> }
                {loading ? "Computing..." : "Run Quantum Solver"}
              </button>
            </div>
            
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col gap-6 min-w-0">
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
                <p className="text-sm font-medium text-center max-w-sm leading-relaxed">Configure the explicit constraints and subtype scores, then run the solver to generate a personalized multidrug regimen.</p>
             </div>
           )}

           {results && (
             <>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 <MetricBox label="Objective Score" value={results.solution.metrics.objective_score.toFixed(2)} />
                 <MetricBox label="Total Toxicity" value={results.solution.metrics.total_toxicity.toFixed(2)} />
               </div>

               <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-6 border border-white/60">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 shadow-inner">
                      <Target size={16} />
                    </div>
                    <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">Optimized Schedule</h3>
                  </div>
                  
                  <ScheduleGrid schedule={results.solution.schedule} days={patientData.days} />
               </div>
               
               <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                 <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-6 border border-white/60 overflow-hidden flex flex-col h-[400px]">
                   <div className="flex items-center gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 shadow-inner">
                        <ActivityIcon size={16} />
                      </div>
                      <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">Toxicity Limit</h3>
                   </div>
                   <div className="flex-1 w-full bg-[#E6EEF5] rounded-2xl shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] p-2 flex items-center justify-center overflow-hidden">
                     <Plot
                        data={[
                          {
                            x: results.charts.t_days,
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
                             y: [results.charts.budget, results.charts.budget],
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

                 <div className="bg-[#E6EEF5] shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] rounded-[2rem] p-6 border border-white/60 flex flex-col h-[400px]">
                   <div className="flex items-center gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 shadow-inner">
                        <Shield size={16} />
                      </div>
                      <h3 className="font-black text-slate-700 uppercase tracking-widest text-sm">Tumor Size Reduction</h3>
                   </div>
                   <div className="flex-1 w-full bg-[#E6EEF5] rounded-2xl shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] p-2 flex justify-center items-center overflow-hidden">
                     <Plot
                        data={[
                          {
                            x: results.charts.t_days,
                            y: results.charts.tumor_std,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Standard Care',
                            line: {color: '#94a3b8', width: 2, dash: 'dash'},
                            marker: {symbol: 'circle', size: 4}
                          },
                          {
                            x: results.charts.t_days,
                            y: results.charts.tumor_qdos,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Q-DOS Optimized',
                            line: {color: '#10b981', width: 3},
                            marker: {symbol: 'diamond', size: 6}
                          }
                        ]}
                        layout={{
                          autosize: true,
                          margin: {l:40, r:20, t:20, b:40},
                          paper_bgcolor: 'rgba(0,0,0,0)',
                          plot_bgcolor: 'rgba(0,0,0,0)',
                          xaxis: {title: 'Days'},
                          yaxis: {title: 'Size (#)'},
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
      <label className="block text-[9px] font-black text-slate-500 uppercase tracking-widest pl-2 mb-1">{label}</label>
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[#E6EEF5] rounded-xl px-3 py-2 text-sm shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] focus:outline-none focus:ring-2 focus:ring-indigo-400 font-bold text-slate-700 transition-all border-none"
      />
    </div>
  );
}

function Slider({ label, value, onChange, ...props }: any) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1 px-2">
        <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{label}</label>
        <span className="text-[10px] font-black text-indigo-500 bg-[#E6EEF5] px-1.5 py-0.5 rounded shadow-[inset_2px_2px_4px_#c4cacf,inset_-2px_-2px_4px_#ffffff]">{value}</span>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        {...props}
        className="w-full h-2 bg-[#E6EEF5] rounded-full appearance-none shadow-[inset_3px_3px_6px_#c4cacf,inset_-3px_-3px_6px_#ffffff] accent-indigo-500 cursor-pointer"
      />
    </div>
  );
}

function MetricBox({ label, value }: { label: string, value: string | number }) {
  return (
    <div className="bg-[#E6EEF5] rounded-[2rem] p-4 shadow-[8px_8px_16px_#c4cacf,-8px_-8px_16px_#ffffff] border border-white/60 flex flex-col items-center justify-center text-center">
       <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">{label}</span>
       <span className="text-3xl font-black text-indigo-600 drop-shadow-sm">{value}</span>
    </div>
  );
}

function ScheduleGrid({ schedule, days }: { schedule: any, days: number }) {
   if (!schedule) return null;
   
   const numDays = days;
   const daysArr = Array.from({length: numDays}, (_, i) => i);

   return (
     <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {daysArr.map(day => {
           const drugsOnDay = Object.keys(schedule).filter(drug => schedule[drug][day] === 1);
           const isRest = drugsOnDay.length === 0;

           return (
             <div key={day} className={cn(
               "h-20 rounded-xl flex flex-col items-center justify-center p-2 text-center transition-all border border-white/40",
               isRest ? "bg-[#E6EEF5] shadow-[inset_4px_4px_8px_#c4cacf,inset_-4px_-4px_8px_#ffffff] text-slate-400"
                      : "bg-indigo-50 shadow-[6px_6px_12px_#c4cacf,-6px_-6px_12px_#ffffff] text-indigo-700 relative overflow-hidden"
             )}>
                {!isRest && <div className="absolute inset-0 bg-indigo-500/5 backdrop-blur-sm" />}
                <span className="text-[9px] font-black uppercase tracking-widest opacity-50 mb-1 relative z-10">Day {day+1}</span>
                <span className="text-[10px] font-bold leading-tight relative z-10 drop-shadow-sm">
                  {isRest ? "Rest" : drugsOnDay.join(" + ")}
                </span>
             </div>
           )
        })}
     </div>
   )
}

export default App;
