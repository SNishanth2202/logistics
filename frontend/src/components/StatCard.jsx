import React from 'react';

export default function StatCard({ 
  label, 
  value, 
  unit = '', 
  icon: Icon, 
  trend, 
  trendPositive, 
  subtext,
  badge
}) {
  return (
    <div className="bg-white rounded-2xl p-5 border border-[#E2E8F0] shadow-subtle hover:shadow-card hover:border-blue-200 transition-smooth group">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-[#64748B]">
          {label}
        </span>
        {Icon && (
          <div className="w-9 h-9 rounded-xl bg-[#E8F3FF] text-[#2563EB] flex items-center justify-center group-hover:scale-105 transition-transform">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl sm:text-3xl font-bold tracking-tight text-[#172033]">
          {value}
        </span>
        {unit && (
          <span className="text-sm font-medium text-[#64748B]">{unit}</span>
        )}
      </div>

      <div className="mt-2.5 flex items-center justify-between text-xs text-[#64748B]">
        {trend && (
          <div className="flex items-center gap-1">
            <span className={`font-semibold ${trendPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
              {trend}
            </span>
            {subtext && <span>{subtext}</span>}
          </div>
        )}
        {!trend && subtext && (
          <span>{subtext}</span>
        )}
        {badge && (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#F0F7FF] text-[#2563EB] border border-blue-100">
            {badge}
          </span>
        )}
      </div>
    </div>
  );
}
