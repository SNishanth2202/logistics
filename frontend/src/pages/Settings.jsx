import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Server, 
  Sliders, 
  Shield, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  ExternalLink,
  Save,
  Cpu
} from 'lucide-react';
import SectionCard from '../components/SectionCard';
import { getStoredBaseUrl, setBaseUrl, checkHealth } from '../services/api';

export default function Settings({ onRefreshHealth, isOnline }) {
  const [apiUrl, setApiUrlState] = useState('http://localhost:8000');
  const [threshold, setThreshold] = useState(0.50);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saveNotice, setSaveNotice] = useState(false);

  useEffect(() => {
    setApiUrlState(getStoredBaseUrl());
    const savedThresh = localStorage.getItem('logix_threshold');
    if (savedThresh) setThreshold(parseFloat(savedThresh));
  }, []);

  const handleSaveApiUrl = () => {
    setBaseUrl(apiUrl);
    setSaveNotice(true);
    setTimeout(() => setSaveNotice(false), 3000);
    onRefreshHealth();
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await checkHealth();
      setTestResult({
        ok: res.ok,
        message: res.ok ? 'Connection established! FastAPI status: 200 OK' : res.error,
      });
    } catch (err) {
      setTestResult({ ok: false, message: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleThresholdChange = (val) => {
    setThreshold(val);
    localStorage.setItem('logix_threshold', val.toString());
  };

  return (
    <div className="space-y-6 max-w-4xl">
      
      <div>
        <h2 className="text-xl font-extrabold text-[#172033] tracking-tight">
          System Settings & Inference Configuration
        </h2>
        <p className="text-xs text-[#64748B] mt-0.5">
          Configure FastAPI endpoint connections, threshold calibration, and live ML runtime parameters.
        </p>
      </div>

      {/* Backend API Configuration */}
      <SectionCard
        title="FastAPI Backend Gateway"
        subtitle="Manage the connection to the Python XGBoost microservice"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#172033] mb-1.5">
              API Base URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrlState(e.target.value)}
                placeholder="http://localhost:8000"
                className="flex-1 px-3.5 py-2.5 border border-[#E2E8F0] rounded-xl text-xs font-mono outline-none focus:border-[#2563EB]"
              />
              <button
                onClick={handleSaveApiUrl}
                className="px-4 py-2.5 bg-[#2563EB] text-white rounded-xl text-xs font-semibold hover:bg-blue-700 transition-colors flex items-center gap-1.5"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save</span>
              </button>
              <button
                onClick={handleTestConnection}
                disabled={testing}
                className="px-4 py-2.5 bg-white border border-[#E2E8F0] text-[#172033] rounded-xl text-xs font-semibold hover:bg-slate-50 transition-colors flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin text-[#2563EB]' : ''}`} />
                <span>Test Ping</span>
              </button>
            </div>
            {saveNotice && (
              <span className="text-[11px] text-emerald-600 font-medium mt-1 block">
                ✓ Endpoint configuration saved to local storage
              </span>
            )}
          </div>

          {testResult && (
            <div className={`p-3.5 rounded-xl border text-xs flex items-center gap-2.5 ${
              testResult.ok ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'
            }`}>
              {testResult.ok ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />}
              <span>{testResult.message}</span>
            </div>
          )}

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              <span>Current Status: <strong className="text-slate-800">{isOnline ? 'Online (HTTP 200)' : 'Offline / Unreachable'}</strong></span>
            </div>
            <a
              href={`${apiUrl}/docs`}
              target="_blank"
              rel="noreferrer"
              className="text-[#2563EB] hover:underline font-semibold flex items-center gap-1 text-[11px]"
            >
              <span>Swagger Docs</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </SectionCard>

      {/* Decision Threshold Slider */}
      <SectionCard
        title="Delay Decision Threshold Calibration"
        subtitle="Control the probability cutoff at which a shipment is flagged as Delayed (default: 0.50)"
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#172033]">Decision Threshold</span>
            <span className="text-base font-extrabold font-mono text-[#2563EB]">{threshold.toFixed(2)}</span>
          </div>

          <input
            type="range"
            min="0.30"
            max="0.70"
            step="0.05"
            value={threshold}
            onChange={(e) => handleThresholdChange(parseFloat(e.target.value))}
            className="w-full accent-[#2563EB] cursor-pointer"
          />

          <div className="flex justify-between text-[11px] text-[#64748B] font-mono">
            <span>0.30 (Higher Recall / More Late Alerts)</span>
            <span>0.50 (Balanced Production)</span>
            <span>0.70 (Higher Precision)</span>
          </div>

          <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-900 leading-relaxed">
            <strong>Operational Note:</strong> In supply chain logistics, the cost of an unexpected delay is often higher than a false alert. Lowering the threshold to <code className="font-bold text-[#2563EB]">0.40</code> increases recall for delayed deliveries from 65.1% to ~76%.
          </div>
        </div>
      </SectionCard>

      {/* System Diagnostics & Platform Overview */}
      <SectionCard
        title="Environment & Artifact Diagnostics"
        subtitle="Installed models, preprocessors, and runtime specifications"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[#64748B] block text-[11px]">Inference Model</span>
            <span className="font-bold text-[#172033] mt-0.5 block">XGBoost Classifier v3.2.0</span>
            <span className="text-[10px] text-slate-500 font-mono">delay_xgboost.pkl</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[#64748B] block text-[11px]">Matching Engine</span>
            <span className="font-bold text-[#172033] mt-0.5 block">Scipy Hungarian Algorithm</span>
            <span className="text-[10px] text-slate-500 font-mono">linear_sum_assignment</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[#64748B] block text-[11px]">Backend Server</span>
            <span className="font-bold text-[#172033] mt-0.5 block">FastAPI / Uvicorn ASGI</span>
            <span className="text-[10px] text-slate-500 font-mono">port 8000</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[#64748B] block text-[11px]">Frontend Stack</span>
            <span className="font-bold text-[#172033] mt-0.5 block">React 18 + Vite + Tailwind CSS</span>
            <span className="text-[10px] text-slate-500 font-mono">LOGIX AI Design System</span>
          </div>
        </div>
      </SectionCard>

    </div>
  );
}
