import React from 'react';
import { RefreshCw, Activity, Menu, ShieldCheck, Cpu } from 'lucide-react';

export default function Header({ 
  title, 
  subtitle, 
  isOnline, 
  isChecking, 
  onRefreshHealth,
  toggleMobileMenu 
}) {
  return (
    <header className="h-16 px-6 bg-white border-b border-[#E2E8F0] flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button 
          onClick={toggleMobileMenu}
          className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-lg font-bold text-[#172033] tracking-tight">{title}</h1>
          {subtitle && (
            <p className="text-xs text-[#64748B] hidden sm:block">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* System Online / Offline Badge */}
        <div 
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
            isOnline 
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
              : 'bg-rose-50 text-rose-700 border-rose-200'
          }`}
        >
          <span className="relative flex h-2 w-2">
            {isOnline && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span className={`relative inline-flex rounded-full h-2 w-2 ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          </span>
          <span className="font-semibold">{isOnline ? 'System Online' : 'API Offline'}</span>
          <span className="text-[10px] opacity-75 hidden md:inline">
            {isOnline ? '• FastAPI :8000' : '• Check Port'}
          </span>
        </div>

        {/* Refresh health check button */}
        <button
          onClick={onRefreshHealth}
          disabled={isChecking}
          title="Verify FastAPI Health"
          className="p-2 rounded-xl text-[#64748B] hover:text-[#172033] hover:bg-[#F8FAFC] border border-[#E2E8F0] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isChecking ? 'animate-spin text-[#2563EB]' : ''}`} />
        </button>

        {/* Demo Viva Mode Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-[#F0F7FF] text-[#2563EB] border border-blue-100 rounded-xl text-xs font-semibold">
          <Cpu className="w-3.5 h-3.5" />
          <span>Production AI</span>
        </div>
      </div>
    </header>
  );
}
