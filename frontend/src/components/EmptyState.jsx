import React from 'react';
import { PackageOpen } from 'lucide-react';

export default function EmptyState({ 
  title = 'No Data Available', 
  message = 'There are no items matching this criteria.', 
  icon: Icon = PackageOpen,
  actionLabel,
  onAction 
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-white border border-dashed border-[#E2E8F0] rounded-2xl">
      <div className="w-12 h-12 rounded-2xl bg-[#F0F7FF] text-[#2563EB] flex items-center justify-center mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-[#172033]">{title}</h3>
      <p className="text-xs text-[#64748B] mt-1 max-w-sm leading-relaxed">{message}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 bg-[#2563EB] text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition-colors shadow-xs"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
