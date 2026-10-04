import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ message = 'Loading data...', subtext = 'Please wait a moment' }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <div className="relative mb-4">
        <div className="w-12 h-12 rounded-full border-4 border-[#E8F3FF] border-t-[#2563EB] animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-[#2563EB]" />
        </div>
      </div>
      <h3 className="text-sm font-semibold text-[#172033]">{message}</h3>
      {subtext && <p className="text-xs text-[#64748B] mt-1 max-w-xs">{subtext}</p>}
    </div>
  );
}
