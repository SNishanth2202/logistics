import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorMessage({ 
  title = 'Operation Failed', 
  message, 
  onRetry 
}) {
  return (
    <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3">
      <div className="w-8 h-8 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center shrink-0 mt-0.5">
        <AlertCircle className="w-4 h-4" />
      </div>
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-rose-900">{title}</h4>
        <p className="text-xs text-rose-700 mt-1 leading-relaxed">
          {message || 'An unexpected error occurred while communicating with the logistics ML server.'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold hover:bg-rose-700 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Try Again</span>
          </button>
        )}
      </div>
    </div>
  );
}
