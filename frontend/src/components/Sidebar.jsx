import React from 'react';
import { 
  LayoutDashboard, 
  AlertTriangle, 
  Truck, 
  BarChart3, 
  BrainCircuit, 
  Settings, 
  Layers,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

export default function Sidebar({ currentTab, setCurrentTab, isOnline }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/' },
    { id: 'delay-prediction', label: 'Delay Prediction', icon: AlertTriangle, path: '/delay-prediction' },
    { id: 'freight-matching', label: 'Freight Matching', icon: Truck, path: '/freight-matching' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/analytics' },
    { id: 'model-performance', label: 'Model Performance', icon: BrainCircuit, path: '/model-performance' },
    { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-[#E2E8F0] flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 px-6 border-b border-[#E2E8F0] flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#2563EB] flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
            <div className="relative">
              <Truck className="w-5 h-5" />
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-sky-300 rounded-full border-2 border-[#2563EB]" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-lg tracking-tight text-[#172033]">LOGIX</span>
              <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-[#E8F3FF] text-[#2563EB]">AI</span>
            </div>
            <p className="text-[11px] font-medium text-[#64748B] -mt-0.5">AI Logistics Platform</p>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="p-4 space-y-1">
          <p className="px-3 pt-2 pb-1.5 text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
            Operations & AI
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-[#E8F3FF] text-[#2563EB] shadow-xs'
                    : 'text-[#64748B] hover:text-[#172033] hover:bg-[#F8FAFC]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 transition-colors ${isActive ? 'text-[#2563EB]' : 'text-[#64748B]'}`} />
                  <span className={isActive ? 'font-semibold text-[#2563EB]' : ''}>{item.label}</span>
                </div>
                {isActive && <ChevronRight className="w-4 h-4 text-[#2563EB]" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer Info Box */}
      <div className="p-4 border-t border-[#E2E8F0] space-y-3">
        <div className="p-3 bg-[#F0F7FF] border border-blue-100 rounded-xl">
          <div className="flex items-center gap-2 mb-1.5">
            <BrainCircuit className="w-4 h-4 text-[#2563EB]" />
            <span className="text-xs font-bold text-[#172033]">XGBoost Production</span>
          </div>
          <p className="text-[11px] text-[#64748B] leading-relaxed">
            Dual-phase delay classifier & Hungarian assignment engine.
          </p>
          <div className="mt-2 pt-2 border-t border-blue-200/50 flex items-center justify-between text-[10px] text-[#64748B]">
            <span>ROC-AUC</span>
            <span className="font-bold text-[#2563EB]">0.8115</span>
          </div>
        </div>

        <div className="flex items-center justify-between px-1 text-[11px] text-[#64748B]">
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-[#16A34A]' : 'bg-[#EF4444]'}`} />
            <span>{isOnline ? 'Backend Online' : 'Backend Offline'}</span>
          </div>
          <span className="font-mono text-[10px] text-slate-400">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
}
