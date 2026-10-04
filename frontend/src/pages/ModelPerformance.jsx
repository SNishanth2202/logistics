import React, { useState } from 'react';
import { 
  BrainCircuit, 
  Target, 
  Award, 
  CheckCircle2, 
  BarChart2, 
  Layers, 
  Sparkles, 
  ZoomIn, 
  Eye, 
  ShieldCheck,
  Cpu,
  Info
} from 'lucide-react';
import SectionCard from '../components/SectionCard';
import StatCard from '../components/StatCard';

const MODEL_BENCHMARK = [
  { model: 'XGBoost (Production)', accuracy: '75.96%', precision: '71.39%', recall: '65.11%', f1: '68.10%', roc_auc: '0.8115', pr_auc: '0.6589', brier: '0.2372', isPrimary: true },
  { model: 'Random Forest', accuracy: '76.34%', precision: '72.42%', recall: '64.56%', f1: '68.26%', roc_auc: '0.8045', pr_auc: '0.6664', brier: '0.1864', isPrimary: false },
  { model: 'Logistic Regression', accuracy: '61.94%', precision: '90.32%', recall: '3.85%', f1: '7.38%', roc_auc: '0.6600', pr_auc: '0.5899', brier: '0.2897', isPrimary: false },
  { model: 'Majority Baseline', accuracy: '60.58%', precision: '0.00%', recall: '0.00%', f1: '0.00%', roc_auc: '0.5000', pr_auc: '0.3942', brier: '0.2425', isPrimary: false },
];

export default function ModelPerformance() {
  const [activeTab, setActiveTab] = useState('curves');
  const [modalImage, setModalImage] = useState(null);

  const tabs = [
    { id: 'curves', label: 'ROC & PR Curves' },
    { id: 'confusion', label: 'Confusion Matrices' },
    { id: 'importance', label: 'Feature Importance' },
    { id: 'shap', label: 'SHAP Explainability' },
    { id: 'eda', label: 'Dataset EDA Figures' },
  ];

  return (
    <div className="space-y-6">
      
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-extrabold text-[#172033] tracking-tight">
          Model Performance & Explainability
        </h2>
        <p className="text-xs text-[#64748B] mt-0.5">
          Empirical evaluation metrics, discrimination curves, confusion matrices, and SHAP interpretability for the production XGBoost classifier.
        </p>
      </div>

      {/* TOP KPI CARDS: ONLY ACTUAL REPOSITORY VALUES */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <StatCard
          label="ROC-AUC"
          value="0.8115"
          subtext="Discrimination score"
          badge="XGBoost"
        />
        <StatCard
          label="Accuracy"
          value="75.96%"
          subtext="Chronological test set"
        />
        <StatCard
          label="Precision"
          value="71.39%"
          subtext="Positive delayed class"
        />
        <StatCard
          label="Recall"
          value="65.11%"
          subtext="Late delivery detection"
        />
        <StatCard
          label="F1-Score"
          value="68.10%"
          subtext="Harmonic mean"
        />
        <StatCard
          label="PR-AUC"
          value="0.6589"
          subtext="Precision-Recall Area"
        />
      </div>

      {/* BENCHMARK COMPARISON TABLE */}
      <SectionCard
        title="Model Benchmark Comparison"
        subtitle="Evaluated strictly on held-out chronological test split (15% chronological partition)"
        action={
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            Source: model_comparison.csv
          </span>
        }
        noPadding
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
                <th className="py-3 px-4">Model Architecture</th>
                <th className="py-3 px-4">ROC-AUC</th>
                <th className="py-3 px-4">Accuracy</th>
                <th className="py-3 px-4">Precision</th>
                <th className="py-3 px-4">Recall</th>
                <th className="py-3 px-4">F1 Score</th>
                <th className="py-3 px-4">PR-AUC</th>
                <th className="py-3 px-4">Brier Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F0]">
              {MODEL_BENCHMARK.map((m, idx) => (
                <tr 
                  key={idx} 
                  className={m.isPrimary ? 'bg-[#F0F7FF]/70 font-semibold text-[#172033]' : 'hover:bg-slate-50 text-[#64748B]'}
                >
                  <td className="py-3.5 px-4 font-medium flex items-center gap-2">
                    {m.isPrimary && (
                      <span className="w-2 h-2 rounded-full bg-[#2563EB]" />
                    )}
                    <span className={m.isPrimary ? 'font-bold text-[#2563EB]' : 'text-[#172033]'}>
                      {m.model}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-800">{m.roc_auc}</td>
                  <td className="py-3.5 px-4 font-mono">{m.accuracy}</td>
                  <td className="py-3.5 px-4 font-mono">{m.precision}</td>
                  <td className="py-3.5 px-4 font-mono">{m.recall}</td>
                  <td className="py-3.5 px-4 font-mono">{m.f1}</td>
                  <td className="py-3.5 px-4 font-mono">{m.pr_auc}</td>
                  <td className="py-3.5 px-4 font-mono">{m.brier}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* VISUALIZATION ARTIFACTS TAB BAR */}
      <div className="flex border-b border-[#E2E8F0] gap-2 overflow-x-auto pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'bg-[#2563EB] text-white shadow-xs'
                : 'text-[#64748B] hover:text-[#172033] hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB CONTENT: ACTUAL ASSETS FROM REPOSITORY */}
      <div>
        {/* TAB 1: ROC & PR CURVES */}
        {activeTab === 'curves' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-[#172033]">ROC Curve Comparison</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-[#2563EB] font-bold">
                    roc_curves.png
                  </span>
                </div>
                <p className="text-xs text-[#64748B] mb-4">
                  Shows True Positive Rate vs False Positive Rate. XGBoost reaches AUC = 0.8115, clearly separating from Majority Baseline (0.50) and Logistic Regression (0.66).
                </p>
              </div>
              <div 
                onClick={() => setModalImage('/figures/roc_curves.png')}
                className="rounded-xl overflow-hidden border border-[#E2E8F0] bg-slate-50 cursor-pointer group relative"
              >
                <img 
                  src="/figures/roc_curves.png" 
                  alt="ROC Curves" 
                  className="w-full h-auto object-contain group-hover:scale-101 transition-transform" 
                />
                <div className="absolute inset-0 bg-slate-900/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span className="px-3 py-1.5 bg-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5">
                    <ZoomIn className="w-3.5 h-3.5" /> Click to Expand
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-[#172033]">Precision-Recall Curves</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-[#2563EB] font-bold">
                    pr_curves.png
                  </span>
                </div>
                <p className="text-xs text-[#64748B] mb-4">
                  PR-AUC is vital for imbalanced delays (35% delayed). XGBoost achieves 0.6589 PR-AUC vs 0.3942 baseline.
                </p>
              </div>
              <div 
                onClick={() => setModalImage('/figures/pr_curves.png')}
                className="rounded-xl overflow-hidden border border-[#E2E8F0] bg-slate-50 cursor-pointer group relative"
              >
                <img 
                  src="/figures/pr_curves.png" 
                  alt="PR Curves" 
                  className="w-full h-auto object-contain group-hover:scale-101 transition-transform" 
                />
                <div className="absolute inset-0 bg-slate-900/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span className="px-3 py-1.5 bg-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5">
                    <ZoomIn className="w-3.5 h-3.5" /> Click to Expand
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: CONFUSION MATRICES */}
        {activeTab === 'confusion' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-bold text-[#172033] mb-1">XGBoost Matrix</h4>
                <p className="text-xs text-[#64748B] mb-3">Balanced true positive (delayed) and true negative (on-time) classifications.</p>
              </div>
              <img 
                src="/figures/confusion_matrix_xgboost.png" 
                alt="XGBoost Confusion Matrix" 
                onClick={() => setModalImage('/figures/confusion_matrix_xgboost.png')}
                className="w-full h-auto rounded-xl border border-[#E2E8F0] cursor-pointer hover:opacity-95" 
              />
            </div>

            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-bold text-[#172033] mb-1">Random Forest Matrix</h4>
                <p className="text-xs text-[#64748B] mb-3">Ensemble benchmark comparison on identical test partition.</p>
              </div>
              <img 
                src="/figures/confusion_matrix_random_forest.png" 
                alt="Random Forest Confusion Matrix" 
                onClick={() => setModalImage('/figures/confusion_matrix_random_forest.png')}
                className="w-full h-auto rounded-xl border border-[#E2E8F0] cursor-pointer hover:opacity-95" 
              />
            </div>

            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-bold text-[#172033] mb-1">Logistic Regression Matrix</h4>
                <p className="text-xs text-[#64748B] mb-3">Severe false negative rate on minority class (3.85% recall).</p>
              </div>
              <img 
                src="/figures/confusion_matrix_logistic_regression.png" 
                alt="Logistic Regression Matrix" 
                onClick={() => setModalImage('/figures/confusion_matrix_logistic_regression.png')}
                className="w-full h-auto rounded-xl border border-[#E2E8F0] cursor-pointer hover:opacity-95" 
              />
            </div>
          </div>
        )}

        {/* TAB 3: FEATURE IMPORTANCE */}
        {activeTab === 'importance' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-[#172033]">Delay Classification Importance</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-[#2563EB]">feature_importance_xgboost.png</span>
                </div>
                <p className="text-xs text-[#64748B] mb-3">
                  Historical delay rates, corridor traffic density, precipitation, and route distance dominate tree split gain.
                </p>
              </div>
              <img 
                src="/figures/feature_importance_xgboost.png" 
                alt="Feature Importance" 
                onClick={() => setModalImage('/figures/feature_importance_xgboost.png')}
                className="w-full h-auto rounded-xl border border-[#E2E8F0] cursor-pointer" 
              />
            </div>

            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-[#172033]">Freight Matching Feature Importance</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-[#2563EB]">matching_importance.png</span>
                </div>
                <p className="text-xs text-[#64748B] mb-3">
                  Weight utilization, overweight penalties, delay probabilities, and vehicle mileage capacity driving compatibility scores.
                </p>
              </div>
              <img 
                src="/figures/matching_importance.png" 
                alt="Matching Feature Importance" 
                onClick={() => setModalImage('/figures/matching_importance.png')}
                className="w-full h-auto rounded-xl border border-[#E2E8F0] cursor-pointer" 
              />
            </div>
          </div>
        )}

        {/* TAB 4: SHAP EXPLAINABILITY */}
        {activeTab === 'shap' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-[#172033]">SHAP Summary Beeswarm Plot</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-[#2563EB]">shap_summary.png</span>
                </div>
                <p className="text-xs text-[#64748B] mb-3">
                  Shows directional contribution of each feature to log-odds of delivery delay (red = high feature value, blue = low).
                </p>
              </div>
              <img 
                src="/figures/shap_summary.png" 
                alt="SHAP Summary Plot" 
                onClick={() => setModalImage('/figures/shap_summary.png')}
                className="w-full h-auto rounded-xl border border-[#E2E8F0] cursor-pointer" 
              />
            </div>

            <div className="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-subtle flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-[#172033]">Mean Absolute SHAP Values</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-[#2563EB]">shap_bar.png</span>
                </div>
                <p className="text-xs text-[#64748B] mb-3">
                  Global feature impact ranking quantifying average absolute marginal contribution per prediction.
                </p>
              </div>
              <img 
                src="/figures/shap_bar.png" 
                alt="SHAP Bar Plot" 
                onClick={() => setModalImage('/figures/shap_bar.png')}
                className="w-full h-auto rounded-xl border border-[#E2E8F0] cursor-pointer" 
              />
            </div>
          </div>
        )}

        {/* TAB 5: EDA FIGURES GALLERY */}
        {activeTab === 'eda' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { file: '/eda/eda_traffic.png', label: 'Traffic Density vs Delays' },
              { file: '/eda/eda_weather.png', label: 'Weather Telemetry Distributions' },
              { file: '/eda/eda_driver.png', label: 'Driver Experience & Ratings' },
              { file: '/eda/eda_route.png', label: 'Route Distance & Duration' },
              { file: '/eda/eda_truck.png', label: 'Truck Capacity & Age Profile' },
              { file: '/eda/eda_historical.png', label: 'Historical Delay Rate Shifts' },
              { file: '/eda/eda_correlation.png', label: 'Feature Correlation Heatmap' },
              { file: '/eda/eda_target.png', label: 'Target Imbalance (65/35)' },
            ].map((img, i) => (
              <div key={i} className="bg-white rounded-xl border border-[#E2E8F0] p-3 shadow-xs">
                <span className="text-[11px] font-bold text-[#172033] block mb-2 truncate">{img.label}</span>
                <img 
                  src={img.file} 
                  alt={img.label} 
                  onClick={() => setModalImage(img.file)}
                  className="w-full h-36 object-cover rounded-lg border border-[#E2E8F0] cursor-pointer hover:opacity-90" 
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* TECHNICAL METHODOLOGY REPORT CARD */}
      <SectionCard
        title="Production ML Architecture & Pipeline Design"
        subtitle="Key engineering practices implemented in the logistics AI system"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-[#64748B]">
          <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0]">
            <h5 className="font-bold text-[#172033] mb-1.5 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-[#2563EB]" />
              Chronological Splitting
            </h5>
            <p className="leading-relaxed">
              Splits data chronologically (70% train, 15% validation, 15% test). Never randomly shuffles time series, preventing cross-temporal data leakage.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0]">
            <h5 className="font-bold text-[#172033] mb-1.5 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Class Imbalance Solution
            </h5>
            <p className="leading-relaxed">
              Configured <code className="text-blue-600 font-mono">scale_pos_weight = 1.87</code> (neg/pos ratio) to counter the 35% delayed class without artificial SMOTE synthesis.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0]">
            <h5 className="font-bold text-[#172033] mb-1.5 flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-amber-600" />
              Hungarian 1:1 Assignment
            </h5>
            <p className="leading-relaxed">
              Utilizes <code className="text-blue-600 font-mono">scipy.optimize.linear_sum_assignment</code> on bipartite compatibility matrices to maximize globally optimal truck assignments.
            </p>
          </div>
        </div>
      </SectionCard>

      {/* Modal for full-resolution image view */}
      {modalImage && (
        <div 
          onClick={() => setModalImage(null)}
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 cursor-pointer"
        >
          <div className="bg-white p-3 rounded-2xl max-w-4xl max-h-[90vh] overflow-auto shadow-2xl border border-slate-200" onClick={(e) => e.stopPropagation()}>
            <img src={modalImage} alt="Expanded Plot" className="w-full h-auto rounded-lg" />
            <div className="mt-3 flex justify-between items-center text-xs">
              <span className="font-mono text-slate-500">{modalImage}</span>
              <button 
                onClick={() => setModalImage(null)}
                className="px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-lg font-semibold text-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
