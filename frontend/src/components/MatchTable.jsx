import React from 'react';
import { CheckCircle2, ChevronRight, Truck, Route, Weight, Award } from 'lucide-react';
import RiskBadge from './RiskBadge';

export default function MatchTable({ assignments, onSelectAssignment, selectedAssignment }) {
  if (!assignments || assignments.length === 0) {
    return null;
  }

  // Helper to format match score (can be raw float or percentage)
  const formatScore = (rawScore) => {
    // Model output might be raw float or logit; if between 0 and 1, show percentage, otherwise normalize
    let scorePct = rawScore;
    if (rawScore > 0 && rawScore <= 1.0) {
      scorePct = Math.round(rawScore * 1000) / 10;
    } else if (rawScore < 0) {
      // logistic conversion for negative logits: 1 / (1 + exp(-x))
      scorePct = Math.round((1 / (1 + Math.exp(-rawScore))) * 1000) / 10;
    } else if (rawScore > 1.0) {
      scorePct = Math.min(99.4, Math.round(rawScore));
    }
    return scorePct;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm border-collapse">
        <thead>
          <tr className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
            <th className="py-3 px-4">Load ID</th>
            <th className="py-3 px-4">Assigned Truck</th>
            <th className="py-3 px-4">Route ID & Dist</th>
            <th className="py-3 px-4">AI Match Score</th>
            <th className="py-3 px-4">Delay Risk</th>
            <th className="py-3 px-4">Cap. Utilization</th>
            <th className="py-3 px-4 text-center">Status</th>
            <th className="py-3 px-4 text-right">Details</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#E2E8F0]">
          {assignments.map((item, idx) => {
            const scorePct = formatScore(item.match_score);
            const isSelected = selectedAssignment && selectedAssignment.load_id === item.load_id;
            const capUtilPct = item.capacity_utilization 
              ? Math.round(item.capacity_utilization * 100) 
              : null;

            // Score badge color
            let scoreBadge = 'bg-blue-50 text-blue-700 border-blue-200';
            if (scorePct >= 80) scoreBadge = 'bg-emerald-50 text-emerald-700 border-emerald-200';
            else if (scorePct >= 50) scoreBadge = 'bg-blue-50 text-blue-700 border-blue-200';
            else scoreBadge = 'bg-amber-50 text-amber-700 border-amber-200';

            return (
              <tr
                key={idx}
                onClick={() => onSelectAssignment(item)}
                className={`cursor-pointer transition-colors ${
                  isSelected 
                    ? 'bg-[#F0F7FF] border-l-4 border-l-[#2563EB]' 
                    : 'hover:bg-[#F8FAFC]'
                }`}
              >
                {/* Load ID */}
                <td className="py-3.5 px-4 font-mono font-bold text-[#172033]">
                  {item.load_id}
                </td>

                {/* Truck ID */}
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-[#E8F3FF] text-[#2563EB] flex items-center justify-center shrink-0">
                      <Truck className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <span className="font-semibold text-[#172033]">
                        TR-{String(item.truck_id).slice(-4)}
                      </span>
                      <span className="block text-[11px] text-[#64748B] font-mono">
                        #{item.truck_id}
                      </span>
                    </div>
                  </div>
                </td>

                {/* Route */}
                <td className="py-3.5 px-4 text-xs text-[#64748B]">
                  <div className="font-semibold text-[#172033]">{item.route_id}</div>
                  {item.distance && (
                    <div className="text-[11px]">{Math.round(item.distance)} miles</div>
                  )}
                </td>

                {/* Match Score */}
                <td className="py-3.5 px-4">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${scoreBadge}`}>
                    <Award className="w-3 h-3" />
                    <span>{scorePct}%</span>
                  </span>
                </td>

                {/* Delay Risk */}
                <td className="py-3.5 px-4">
                  <RiskBadge probability={item.delay_probability} size="sm" />
                </td>

                {/* Capacity Utilization */}
                <td className="py-3.5 px-4">
                  {capUtilPct !== null ? (
                    <div className="w-28">
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="font-medium text-[#172033]">{capUtilPct}%</span>
                        <span className="text-slate-400">capacity</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            capUtilPct > 100 ? 'bg-rose-500' : capUtilPct > 85 ? 'bg-blue-600' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, capUtilPct)}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>

                {/* Status */}
                <td className="py-3.5 px-4 text-center">
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Matched</span>
                  </span>
                </td>

                {/* Action arrow */}
                <td className="py-3.5 px-4 text-right">
                  <button className="p-1 rounded-lg text-slate-400 hover:text-[#2563EB] hover:bg-white">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
