import React, { useState, useEffect } from 'react';
import { 
  Truck, 
  Package, 
  Play, 
  Sparkles, 
  CheckSquare, 
  Square, 
  Plus, 
  RefreshCw, 
  Layers, 
  Cpu, 
  CheckCircle2, 
  AlertTriangle,
  Award
} from 'lucide-react';
import SectionCard from '../components/SectionCard';
import MatchTable from '../components/MatchTable';
import AssignmentDrawer from '../components/AssignmentDrawer';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import { getSampleData, matchFreight } from '../services/api';

export default function FreightMatching() {
  const [loads, setLoads] = useState([]);
  const [trucks, setTrucks] = useState([]);
  const [selectedTruckIds, setSelectedTruckIds] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [loadingData, setLoadingData] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState(null);
  const [successNotice, setSuccessNotice] = useState(null);

  // New load modal state
  const [showAddLoad, setShowAddLoad] = useState(false);
  const [newLoad, setNewLoad] = useState({
    load_id: `LOAD-${Math.floor(1000 + Math.random() * 9000)}`,
    route_id: 'R-b236e347',
    departure_date: '2019-02-15 08:00:00',
    load_weight_pounds: 6500.0,
    distance: 310.75,
  });

  const loadData = async () => {
    setLoadingData(true);
    setError(null);
    try {
      const data = await getSampleData();
      if (data && data.loads && data.trucks) {
        setLoads(data.loads);
        setTrucks(data.trucks);
        // Select top 6 trucks by default
        setSelectedTruckIds(data.trucks.slice(0, 6).map((t) => t.truck_id));
      }
    } catch (err) {
      setError(err.message || 'Failed to load fleet and freight records from backend.');
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const toggleTruckSelection = (truckId) => {
    setSelectedTruckIds((prev) =>
      prev.includes(truckId) ? prev.filter((id) => id !== truckId) : [...prev, truckId]
    );
  };

  const selectAllTrucks = () => {
    setSelectedTruckIds(trucks.map((t) => t.truck_id));
  };

  const handleRunMatching = async () => {
    if (loads.length === 0) {
      setError('Please provide at least one load to assign.');
      return;
    }
    if (selectedTruckIds.length === 0) {
      setError('Please select at least one available truck for matching.');
      return;
    }

    setOptimizing(true);
    setError(null);
    setSuccessNotice(null);

    try {
      // Map loads strictly to API schema: load_id, route_id, departure_date, load_weight_pounds
      const formattedLoads = loads.map((l) => ({
        load_id: l.load_id,
        route_id: l.route_id,
        departure_date: l.departure_date,
        load_weight_pounds: parseFloat(l.load_weight_pounds),
      }));

      const res = await matchFreight(formattedLoads, selectedTruckIds);
      if (res && res.assignments) {
        setAssignments(res.assignments);
        setSuccessNotice(`Successfully solved global 1:1 optimization for ${res.assignments.length} assignments.`);
        // Auto-select first assignment for drawer review
        if (res.assignments.length > 0) {
          setSelectedAssignment(res.assignments[0]);
        }
      } else {
        setAssignments([]);
      }
    } catch (err) {
      setError(err.message || 'Matching optimization failed.');
    } finally {
      setOptimizing(false);
    }
  };

  const handleCreateLoad = (e) => {
    e.preventDefault();
    setLoads((prev) => [newLoad, ...prev]);
    setShowAddLoad(false);
    setNewLoad({
      load_id: `LOAD-${Math.floor(1000 + Math.random() * 9000)}`,
      route_id: 'R-ada2a391',
      departure_date: '2019-02-15 10:00:00',
      load_weight_pounds: 8000.0,
      distance: 1735.06,
    });
  };

  if (loadingData) {
    return <LoadingSpinner message="Loading Available Freight & Fleet Assets..." subtext="Syncing with logistics schedule and driver records" />;
  }

  return (
    <div className="space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-[#172033] tracking-tight">
            AI Freight Matching & Optimization
          </h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            Find the optimal truck for every pending shipment using XGBoost compatibility scoring and Hungarian linear sum assignment.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddLoad(true)}
            className="px-3.5 py-2 bg-white border border-[#E2E8F0] hover:border-blue-300 text-xs font-semibold rounded-xl text-[#172033] transition-colors shadow-xs flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>Add Custom Load</span>
          </button>

          <button
            onClick={handleRunMatching}
            disabled={optimizing}
            className="px-5 py-2 bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 flex items-center gap-2"
          >
            {optimizing ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Optimizing Assignments...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Run AI Matching</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error & Success Alerts */}
      {error && (
        <ErrorMessage title="Matching Error" message={error} onRetry={handleRunMatching} />
      )}
      {successNotice && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-semibold">{successNotice}</span>
          </div>
          <span className="text-[11px] font-mono text-emerald-700">Hungarian Maximize = True</span>
        </div>
      )}

      {/* MATCHING RESULTS SECTION (When generated) */}
      {assignments.length > 0 && (
        <SectionCard
          title="Optimal AI Assignments"
          subtitle={`Globally optimized ${assignments.length} assignments to maximize compatibility while mitigating corridor delay risk`}
          action={
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-[#2563EB] border border-blue-200">
              Scipy Hungarian Engine
            </span>
          }
          noPadding
        >
          <MatchTable
            assignments={assignments}
            onSelectAssignment={(a) => setSelectedAssignment(a)}
            selectedAssignment={selectedAssignment}
          />
        </SectionCard>
      )}

      {/* TWO COLUMN GRID: LOADS & TRUCKS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* AVAILABLE LOADS (7 cols) */}
        <div className="lg:col-span-6">
          <SectionCard
            title={`Available Loads (${loads.length})`}
            subtitle="Pending shipments requiring dedicated commercial truck assignment"
            action={
              <button
                onClick={loadData}
                title="Reload Schedule Data"
                className="p-1.5 rounded-lg text-slate-400 hover:text-[#2563EB] hover:bg-slate-100"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            }
            noPadding
          >
            {loads.length === 0 ? (
              <EmptyState title="No Freight Available" message="There are currently no pending shipments in the dispatch queue." />
            ) : (
              <div className="divide-y divide-[#E2E8F0] max-h-[460px] overflow-y-auto">
                {loads.map((load, i) => (
                  <div key={i} className="p-4 hover:bg-[#F8FAFC] transition-colors flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#E8F3FF] text-[#2563EB] flex items-center justify-center shrink-0">
                        <Package className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-xs text-[#172033]">{load.load_id}</span>
                          <span className="text-[10px] px-2 py-0.2 bg-slate-100 text-slate-600 rounded">
                            {load.route_id}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#64748B] mt-0.5">
                          {Math.round(load.load_weight_pounds).toLocaleString()} lbs • Departure: {String(load.departure_date).slice(0, 16)}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 shrink-0">
                      Pending
                    </span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        {/* AVAILABLE TRUCKS (5 cols) */}
        <div className="lg:col-span-6">
          <SectionCard
            title={`Fleet Assets (${selectedTruckIds.length}/${trucks.length} Selected)`}
            subtitle="Available commercial fleet units ready for immediate corridor dispatch"
            action={
              <button
                onClick={selectAllTrucks}
                className="text-xs text-[#2563EB] hover:underline font-semibold"
              >
                Select All
              </button>
            }
            noPadding
          >
            {trucks.length === 0 ? (
              <EmptyState title="No Trucks Available" message="No fleet assets are currently marked as available." />
            ) : (
              <div className="divide-y divide-[#E2E8F0] max-h-[460px] overflow-y-auto">
                {trucks.map((truck) => {
                  const isChecked = selectedTruckIds.includes(truck.truck_id);
                  return (
                    <div 
                      key={truck.truck_id}
                      onClick={() => toggleTruckSelection(truck.truck_id)}
                      className={`p-4 cursor-pointer transition-colors flex items-center justify-between gap-3 ${
                        isChecked ? 'bg-[#F0F7FF]/50' : 'hover:bg-[#F8FAFC]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <button className="text-[#2563EB] mt-0.5 shrink-0">
                          {isChecked ? (
                            <CheckSquare className="w-4 h-4 fill-[#2563EB] text-white" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-300" />
                          )}
                        </button>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-[#172033]">
                              TR-{String(truck.truck_id).slice(-4)}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              #{truck.truck_id}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.2 bg-blue-50 text-[#2563EB] rounded font-medium">
                              {truck.fuel_type}
                            </span>
                          </div>
                          <p className="text-[11px] text-[#64748B] mt-0.5">
                            Driver: <strong className="text-slate-700 font-medium">{truck.driver_name}</strong> • Cap: {Math.round(truck.load_capacity_pounds).toLocaleString()} lbs • Rating: {truck.driver_ratings || 7.0}/10
                          </p>
                        </div>
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                        Available
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </SectionCard>
        </div>

      </div>

      {/* Floating or fixed Assignment detail drawer */}
      {selectedAssignment && (
        <AssignmentDrawer
          assignment={selectedAssignment}
          onClose={() => setSelectedAssignment(null)}
        />
      )}

      {/* Modal: Add Custom Load */}
      {showAddLoad && (
        <div className="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-[#E2E8F0]">
            <h3 className="text-base font-bold text-[#172033]">Add Custom Freight Load</h3>
            <p className="text-xs text-[#64748B] mt-0.5">Queue a new cargo load for AI matching assignment.</p>

            <form onSubmit={handleCreateLoad} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">Load ID</label>
                <input
                  type="text"
                  value={newLoad.load_id}
                  onChange={(e) => setNewLoad({ ...newLoad, load_id: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-xl text-xs outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">Route ID (from routes_table)</label>
                <input
                  type="text"
                  value={newLoad.route_id}
                  onChange={(e) => setNewLoad({ ...newLoad, route_id: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-xl text-xs outline-none focus:border-[#2563EB]"
                />
                <span className="text-[10px] text-[#64748B]">e.g. R-b236e347, R-ada2a391, R-ae0ef31f</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">Departure Timestamp</label>
                <input
                  type="text"
                  value={newLoad.departure_date}
                  onChange={(e) => setNewLoad({ ...newLoad, departure_date: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-xl text-xs outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">Load Weight (lbs)</label>
                <input
                  type="number"
                  value={newLoad.load_weight_pounds}
                  onChange={(e) => setNewLoad({ ...newLoad, load_weight_pounds: parseFloat(e.target.value) })}
                  required
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-xl text-xs outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddLoad(false)}
                  className="px-4 py-2 border border-[#E2E8F0] rounded-xl text-xs font-semibold text-[#64748B] hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#2563EB] text-white rounded-xl text-xs font-semibold hover:bg-blue-700"
                >
                  Add to Queue
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
