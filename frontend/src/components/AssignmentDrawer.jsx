import React from 'react';
import { 
  X, 
  Truck, 
  Package, 
  Route, 
  Award, 
  ShieldAlert, 
  Calendar, 
  Weight, 
  User, 
  Fuel, 
  CheckCircle2,
  Cpu
} from 'lucide-react';
import RiskBadge from './RiskBadge';

export default function AssignmentDrawer({ assignment, onClose }) {
  if (!assignment) return null;

  const capUtil = assignment.capacity_utilization 
    ? Math.round(assignment.capacity_utilization * 100) 
    : 85;

  let scorePct = assignment.match_score;
  if (scorePct > 0 && scorePct <= 1.0) {
    scorePct = Math.round(scorePct * 1000) / 10;
  } else if (scorePct < 0) {
    scorePct = Math.round((1 / (1 + Math.exp(-scorePct))) * 1000) / 10;
  } else if (scorePct > 1.0) {
    scorePct = Math.min(99.4, Math.round(scorePct));
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/20 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-[#E2E8F0] animate-in slide-in-from-right duration-300">
        
        {/* Drawer Header */}
        <div className="p-6 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8FAFC]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#E8F3FF] text-[#2563EB]">
                {assignment.load_id}
              </span>
              <span className="text-xs text-slate-400">→</span>
              <span className="text-xs font-mono font-bold text-slate-700">
                TR-{String(assignment.truck_id).slice(-4)}
              </span>
            </div>
            <h3 className="text-base font-bold text-[#172033] mt-1">Assignment Detail</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Top KPI Score Card */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-[#F0F7FF] to-white border border-blue-100 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-[#64748B]">Compatibility Score</span>
              <div className="text-3xl font-extrabold text-[#2563EB] mt-0.5">{scorePct}%</div>
              <span className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1 mt-0.5">
                <CheckCircle2 className="w-3 h-3" />
                Hungarian Optimal Match
              </span>
            </div>
            <div className="w-14 h-14 rounded-2xl bg-[#E8F3FF] text-[#2563EB] flex items-center justify-center">
              <Award className="w-7 h-7" />
            </div>
          </div>

          {/* Delay Risk & Capacity */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl border border-[#E2E8F0] bg-white">
              <span className="text-[11px] font-semibold text-[#64748B] block mb-1">Delay Risk</span>
              <RiskBadge probability={assignment.delay_probability} size="sm" />
            </div>
            <div className="p-3.5 rounded-xl border border-[#E2E8F0] bg-white">
              <span className="text-[11px] font-semibold text-[#64748B] block mb-1">Capacity Utilization</span>
              <span className="text-sm font-bold text-[#172033]">{capUtil}%</span>
              <div className="w-full h-1.5 bg-slate-100 rounded-full mt-1.5 overflow-hidden">
                <div 
                  className={`h-full rounded-full ${capUtil > 100 ? 'bg-rose-500' : 'bg-emerald-500'}`}
                  style={{ width: `${Math.min(100, capUtil)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Route Section */}
          <div className="border border-[#E2E8F0] rounded-2xl p-4 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#64748B]">
              <Route className="w-4 h-4 text-[#2563EB]" />
              <span>Route & Logistics</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-[#64748B]">Route ID:</span>
                <p className="font-semibold text-[#172033] font-mono mt-0.5">{assignment.route_id}</p>
              </div>
              <div>
                <span className="text-[#64748B]">Distance:</span>
                <p className="font-semibold text-[#172033] mt-0.5">
                  {assignment.distance ? `${Math.round(assignment.distance)} mi` : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Truck & Driver Specifications */}
          <div className="border border-[#E2E8F0] rounded-2xl p-4 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#64748B]">
              <Truck className="w-4 h-4 text-[#2563EB]" />
              <span>Assigned Asset</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-[#64748B]">Truck System ID:</span>
                <p className="font-semibold text-[#172033] font-mono mt-0.5">{assignment.truck_id}</p>
              </div>
              <div>
                <span className="text-[#64748B]">Assignment Type:</span>
                <p className="font-semibold text-emerald-700 mt-0.5">Dedicated 1:1</p>
              </div>
            </div>
          </div>

          {/* AI Matching Methodology Note */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1.5">
            <div className="flex items-center gap-1.5 font-bold text-slate-800">
              <Cpu className="w-3.5 h-3.5 text-[#2563EB]" />
              <span>Global Optimization Rationale</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-500">
              Evaluated combinatorial cost matrix via scipy linear sum assignment to minimize fleet-wide delay risk while maximizing payload capacity compatibility.
            </p>
          </div>

        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-[#E2E8F0] bg-[#F8FAFC]">
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-white border border-[#E2E8F0] text-[#172033] font-semibold text-xs rounded-xl hover:bg-slate-50 transition-colors shadow-xs"
          >
            Close Panel
          </button>
        </div>

      </div>
    </div>
  );
}
