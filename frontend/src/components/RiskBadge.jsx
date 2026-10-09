import React from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function RiskBadge({ probability, riskLevel, showIcon = true, size = 'md' }) {
  // If probability is passed (e.g. 0.78 or 78)
  let level = riskLevel;
  let probVal = null;

  if (probability !== undefined && probability !== null) {
    probVal = probability <= 1 ? Math.round(probability * 100) : Math.round(probability);
    if (probVal >= 60) level = 'high';
    else if (probVal >= 40) level = 'medium';
    else level = 'low';
  }

  const configs = {
    low: {
      label: 'Low Delay Risk',
      bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      dot: 'bg-emerald-500',
      icon: CheckCircle2,
    },
    medium: {
      label: 'Medium Delay Risk',
      bg: 'bg-amber-50 text-amber-700 border-amber-200',
      dot: 'bg-amber-500',
      icon: AlertTriangle,
    },
    high: {
      label: 'High Delay Risk',
      bg: 'bg-rose-50 text-rose-700 border-rose-200',
      dot: 'bg-rose-500',
      icon: AlertCircle,
    },
  };

  const current = configs[level] || configs.low;
  const Icon = current.icon;

  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-semibold',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${current.bg} ${sizeClasses[size] || sizeClasses.md}`}>
      {showIcon && <Icon className="w-3.5 h-3.5 shrink-0" />}
      <span>
        {probVal !== null ? `${probVal}% ${current.label}` : current.label}
      </span>
    </span>
  );
}
