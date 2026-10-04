import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import DelayPrediction from './pages/DelayPrediction';
import FreightMatching from './pages/FreightMatching';
import Analytics from './pages/Analytics';
import ModelPerformance from './pages/ModelPerformance';
import Settings from './pages/Settings';
import { checkHealth } from './services/api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [isOnline, setIsOnline] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const verifyHealth = async () => {
    setIsChecking(true);
    try {
      const res = await checkHealth();
      setIsOnline(res.ok);
    } catch {
      setIsOnline(false);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    verifyHealth();
    // Poll health check every 15 seconds
    const interval = setInterval(verifyHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const pageMeta = {
    'dashboard': {
      title: 'Dashboard',
      subtitle: 'Monitor your logistics network with AI-powered insights.',
    },
    'delay-prediction': {
      title: 'Freight Delay Prediction',
      subtitle: 'Predict shipment delay probabilities using calibrated XGBoost inference.',
    },
    'freight-matching': {
      title: 'AI Freight Matching',
      subtitle: 'Find optimal truck assignments with Hungarian combinatorial optimization.',
    },
    'analytics': {
      title: 'Analytics',
      subtitle: 'Explore logistics performance, traffic correlations, and empirical shipment trends.',
    },
    'model-performance': {
      title: 'Model Performance & Explainability',
      subtitle: 'Evaluate model metrics, ROC/PR curves, confusion matrices, and SHAP interpretability.',
    },
    'settings': {
      title: 'Settings',
      subtitle: 'Configure backend microservices and inference thresholds.',
    },
  };

  const currentMeta = pageMeta[currentTab] || pageMeta['dashboard'];

  return (
    <div className="flex h-screen bg-[#F7FAFC] overflow-hidden text-[#172033]">
      
      {/* Desktop Persistent Sidebar */}
      <div className="hidden lg:block shrink-0">
        <Sidebar 
          currentTab={currentTab} 
          setCurrentTab={setCurrentTab} 
          isOnline={isOnline} 
        />
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 z-50 bg-slate-900/40 lg:hidden flex"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div 
            className="w-64 bg-white h-full shadow-2xl" 
            onClick={(e) => e.stopPropagation()}
          >
            <Sidebar 
              currentTab={currentTab} 
              setCurrentTab={(tab) => {
                setCurrentTab(tab);
                setMobileMenuOpen(false);
              }} 
              isOnline={isOnline} 
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Top Header */}
        <Header
          title={currentMeta.title}
          subtitle={currentMeta.subtitle}
          isOnline={isOnline}
          isChecking={isChecking}
          onRefreshHealth={verifyHealth}
          toggleMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)}
        />

        {/* Dynamic Page Container */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'dashboard' && <Dashboard setCurrentTab={setCurrentTab} />}
            {currentTab === 'delay-prediction' && <DelayPrediction />}
            {currentTab === 'freight-matching' && <FreightMatching />}
            {currentTab === 'analytics' && <Analytics />}
            {currentTab === 'model-performance' && <ModelPerformance />}
            {currentTab === 'settings' && <Settings onRefreshHealth={verifyHealth} isOnline={isOnline} />}
          </div>
        </main>

      </div>
    </div>
  );
}
