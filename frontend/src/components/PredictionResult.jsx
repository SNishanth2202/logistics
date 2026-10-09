import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  AlertOctagon, 
  Clock, 
  TrendingUp, 
  ShieldAlert, 
  Lightbulb, 
  ArrowRight,
  Gauge,
  Activity
} from 'lucide-react';

export default function PredictionResult({ result, inputRecord }) {
  if (!result) return null;

  const prob = typeof result.delay_probability === 'number' ? result.delay_probability : 0.0;
  const probPercent = Math.round(prob * 100);
  const onTimePercent = Math.max(0, 100 - probPercent);
  const isDelayed = result.predicted_class === 1;

  // Determine risk category
  let riskLevel = 'Low';
  let badgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  let progressColor = 'bg-[#16A34A]';
  let glowColor = 'from-emerald-500/10 to-transparent';
  let Icon = CheckCircle2;

  if (probPercent >= 60) {
    riskLevel = 'High';
    badgeColor = 'bg-rose-50 text-rose-700 border-rose-200';
    progressColor = 'bg-[#EF4444]';
    glowColor = 'from-rose-500/10 to-transparent';
    Icon = AlertOctagon;
  } else if (probPercent >= 40) {
    riskLevel = 'Medium';
    badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
    progressColor = 'bg-[#F59E0B]';
    glowColor = 'from-amber-500/10 to-transparent';
    Icon = AlertTriangle;
  }

  // Derive risk factors dynamically from actual input features
  const factors = [];
  if (inputRecord) {
    if (inputRecord.traffic_vehicles && inputRecord.traffic_vehicles > 800) {
      factors.push({
        title: 'High Traffic Congestion',
        desc: `Recorded ${inputRecord.traffic_vehicles.toLocaleString()} vehicles/hr on corridor. Peak congestion elevates transit variance.`,
        severity: 'high'
      });
    }
    if (inputRecord.traffic_accident === 1 || inputRecord.daily_accident_count > 0) {
      factors.push({
        title: 'Reported Corridor Incident',
        desc: 'Active accident reported along route segments, introducing bottleneck delays.',
        severity: 'high'
      });
    }
    if (inputRecord.weather_precip && inputRecord.weather_precip > 1.5) {
      factors.push({
        title: 'Adverse Weather / Precipitation',
        desc: `${inputRecord.weather_precip}mm rainfall recorded with reduced tire traction and visibility.`,
        severity: 'medium'
      });
    }
    if (inputRecord.weather_wind_speed && inputRecord.weather_wind_speed > 20) {
      factors.push({
        title: 'Elevated Wind Speeds',
        desc: `${inputRecord.weather_wind_speed} km/h crosswinds require speed reduction for loaded commercial freight.`,
        severity: 'medium'
      });
    }
    if (inputRecord.truck_delay_rate_hist && inputRecord.truck_delay_rate_hist > 0.40) {
      factors.push({
        title: 'Historical Asset Delay Baseline',
        desc: `Assigned truck has a historical delay frequency of ${(inputRecord.truck_delay_rate_hist * 100).toFixed(0)}%.`,
        severity: 'medium'
      });
    }
    if (inputRecord.distance && inputRecord.distance > 1200) {
      factors.push({
        title: 'Long-Haul Corridor (>1,200 mi)',
        desc: `Total transit distance is ${inputRecord.distance.toLocaleString()} miles, increasing exposure to dynamic route disruptions.`,
        severity: 'low'
      });
    }
  }

  // Fallback factors if inputs are default
  if (factors.length === 0) {
    if (probPercent >= 50) {
      factors.push({
        title: 'Combined Operational Variance',
        desc: 'Corridor traffic volume and scheduled transit window align with peak historical delay clusters.',
        severity: 'medium'
      });
    } else {
      factors.push({
        title: 'Optimal Fleet & Route Metrics',
        desc: 'Low corridor traffic density and favorable weather conditions align with high on-time delivery.',
        severity: 'low'
      });
    }
  }

  return (
    <div className="space-y-6">
      {/* Primary Result Banner */}
      <div className={`relative overflow-hidden rounded-2xl border border-[#E2E8F0] bg-white p-6 sm:p-8 shadow-card`}>
        <div className={`absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl ${glowColor} rounded-full blur-3xl pointer-events-none -mr-20 -mt-20`} />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
                AI PREDICTION RESULT
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                XGBoost Model
              </span>
            </div>

            <div className="flex items-baseline gap-4">
              <span className="text-4xl sm:text-5xl font-black tracking-tight text-[#172033]">
                {probPercent}%
              </span>
              <div className="flex flex-col">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${badgeColor}`}>
                  <Icon className="w-3.5 h-3.5" />
                  {riskLevel.toUpperCase()} DELAY RISK
                </span>
                <span className="text-xs text-[#64748B] mt-1 font-medium">
                  Binary Classification: <span className="font-semibold text-[#172033]">{isDelayed ? 'Delayed (>0.50 threshold)' : 'On-Time (<0.50 threshold)'}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Quick Metrics split */}
          <div className="grid grid-cols-2 gap-3 shrink-0">
            <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3.5 text-center min-w-[120px]">
              <span className="text-[11px] font-medium text-[#64748B] block">Delay Probability</span>
              <span className="text-xl font-bold text-rose-600">{probPercent}%</span>
            </div>
            <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3.5 text-center min-w-[120px]">
              <span className="text-[11px] font-medium text-[#64748B] block">On-Time Probability</span>
              <span className="text-xl font-bold text-emerald-600">{onTimePercent}%</span>
            </div>
          </div>
        </div>

        {/* Probability Progress Bar */}
        <div className="mt-6 relative z-10">
          <div className="flex justify-between text-xs font-semibold text-[#64748B] mb-2">
            <span>Probability of Delay</span>
            <span>{probPercent}% (raw: {prob.toFixed(4)})</span>
          </div>
          <div className="w-full h-3.5 bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200">
            <div 
              className={`h-full rounded-full transition-all duration-700 ${progressColor}`}
              style={{ width: `${probPercent}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
            <span>0% (Safe)</span>
            <span>50% (Decision Boundary)</span>
            <span>100% (High Risk)</span>
          </div>
        </div>
      </div>

      {/* Grid: Risk Factors & Recommended Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Identified Risk Factors */}
        <div className="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-subtle">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#E2E8F0]">
            <ShieldAlert className="w-4 h-4 text-[#2563EB]" />
            <h4 className="text-sm font-bold text-[#172033]">Corridor Risk Factors</h4>
          </div>

          <div className="space-y-3">
            {factors.map((f, i) => (
              <div key={i} className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] flex items-start gap-3">
                <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                  f.severity === 'high' ? 'bg-[#EF4444]' : f.severity === 'medium' ? 'bg-[#F59E0B]' : 'bg-[#16A34A]'
                }`} />
                <div>
                  <h5 className="text-xs font-bold text-[#172033]">{f.title}</h5>
                  <p className="text-xs text-[#64748B] mt-0.5 leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommended Action */}
        <div className="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-subtle">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#E2E8F0]">
            <Lightbulb className="w-4 h-4 text-[#F59E0B]" />
            <h4 className="text-sm font-bold text-[#172033]">AI Recommended Actions</h4>
          </div>

          <div className="space-y-3">
            {probPercent >= 60 ? (
              <>
                <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 leading-relaxed">
                  <strong className="block font-bold mb-0.5">Reschedule Departure Window:</strong>
                  Shift scheduled departure by 2 hours to exit peak highway traffic density and reduce congestion risk.
                </div>
                <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-900 leading-relaxed">
                  <strong className="block font-bold mb-0.5">Asset Reallocation:</strong>
                  Evaluate assigning a truck with higher mileage efficiency or a driver with top proactive driving rating.
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
                  <strong className="block font-bold mb-0.5">Buffer Adjustment:</strong>
                  Incorporate a 45-minute buffer into customer SLA delivery promises.
                </div>
              </>
            ) : probPercent >= 40 ? (
              <>
                <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-900 leading-relaxed">
                  <strong className="block font-bold mb-0.5">Active Route Monitoring:</strong>
                  Enable GPS waypoint tracking and real-time weather alerts along key interstate segments.
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
                  <strong className="block font-bold mb-0.5">Driver Pre-Trip Briefing:</strong>
                  Notify driver regarding scheduled slowdowns near urban interchange hubs.
                </div>
              </>
            ) : (
              <>
                <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-900 leading-relaxed">
                  <strong className="block font-bold mb-0.5">Clear for Immediate Dispatch:</strong>
                  Corridor indicators demonstrate optimal weather and free-flowing traffic conditions.
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
                  <strong className="block font-bold mb-0.5">Standard SLA Protocol:</strong>
                  Shipment qualifies for standard on-time guarantee.
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
