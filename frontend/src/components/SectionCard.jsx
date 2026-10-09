import React from 'react';

export default function SectionCard({ 
  title, 
  subtitle, 
  action, 
  children, 
  className = '',
  noPadding = false 
}) {
  return (
    <div className={`bg-white rounded-2xl border border-[#E2E8F0] shadow-subtle ${className}`}>
      {(title || subtitle || action) && (
        <div className="px-6 py-4.5 border-b border-[#E2E8F0] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            {title && <h3 className="text-base font-bold text-[#172033] tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-[#64748B] mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-6'}>
        {children}
      </div>
    </div>
  );
}
