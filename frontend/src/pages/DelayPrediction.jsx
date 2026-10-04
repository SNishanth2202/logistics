import React, { useState } from 'react';
import { 
  AlertTriangle, 
  MapPin, 
  Truck, 
  User, 
  CloudRain, 
  History, 
  Play, 
  Sparkles, 
  RotateCcw,
  Info
} from 'lucide-react';
import SectionCard from '../components/SectionCard';
import PredictionResult from '../components/PredictionResult';
import ErrorMessage from '../components/ErrorMessage';
import { predictDelay } from '../services/api';

// Baseline example from predict.py
const DEFAULT_FORM = {
  departure_date: '2019-02-10T07:00',
  distance: 1200.0,
  average_hours: 24.0,
  traffic_vehicles: 850.0,
  traffic_accident: 0,
  daily_accident_count: 1,

  // Truck
  truck_age: 8,
  load_capacity_pounds: 20000.0,
  mileage_mpg: 18.0,
  fuel_type: 'diesel',

  // Driver
  driver_age: 42,
  experience: 10,
  driver_ratings: 7.0,
  average_speed_mph: 58.5,
  driving_style: 'proactive',

  // Weather
  weather_temp: 28.0,
  weather_wind_speed: 15.0,
  weather_precip: 2.5,
  weather_humidity: 75.0,
  weather_visibility: 6.0,
  weather_chanceofrain: 60.0,
  weather_chanceoffog: 10.0,
  weather_chanceofsnow: 0.0,
  weather_chanceofthunder: 5.0,

  // Historical
  truck_trip_count_hist: 15,
  truck_delay_rate_hist: 0.35,
  route_trip_count_hist: 50,
  route_delay_rate_hist: 0.28,
};

const HIGH_RISK_PRESET = {
  ...DEFAULT_FORM,
  departure_date: '2019-02-14T17:30',
  distance: 1850.0,
  average_hours: 38.0,
  traffic_vehicles: 1350.0,
  traffic_accident: 1,
  daily_accident_count: 3,
  weather_temp: 2.0,
  weather_wind_speed: 32.0,
  weather_precip: 18.5,
  weather_humidity: 94.0,
  weather_visibility: 2.0,
  weather_chanceofrain: 95.0,
  weather_chanceoffog: 70.0,
  weather_chanceofsnow: 45.0,
  truck_delay_rate_hist: 0.62,
  route_delay_rate_hist: 0.58,
};

const LOW_RISK_PRESET = {
  ...DEFAULT_FORM,
  departure_date: '2019-02-12T10:00',
  distance: 350.0,
  average_hours: 6.5,
  traffic_vehicles: 320.0,
  traffic_accident: 0,
  daily_accident_count: 0,
  experience: 18,
  driver_ratings: 9.5,
  driving_style: 'proactive',
  weather_temp: 22.0,
  weather_wind_speed: 6.0,
  weather_precip: 0.0,
  weather_humidity: 45.0,
  weather_visibility: 10.0,
  weather_chanceofrain: 0.0,
  weather_chanceoffog: 0.0,
  weather_chanceofsnow: 0.0,
  truck_delay_rate_hist: 0.12,
  route_delay_rate_hist: 0.15,
};

export default function DelayPrediction() {
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value,
    }));
  };

  const handlePredict = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Prepare payload formatted strictly to API record schema
      const formattedDate = formData.departure_date.replace('T', ' ') + ':00';
      const record = {
        ...formData,
        departure_date: formattedDate,
      };

      const res = await predictDelay(record);
      setResult(res);
      // Smooth scroll to result
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(err.message || 'Delay prediction failed. Ensure FastAPI is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-[#172033] tracking-tight">
            Freight Delay Prediction
          </h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            Predict the probability of shipment delay using our XGBoost machine learning model.
          </p>
        </div>

        {/* Demo Scenario Presets */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-[#64748B] mr-1 hidden sm:inline">
            Load Preset:
          </span>
          <button
            type="button"
            onClick={() => setFormData(DEFAULT_FORM)}
            className="px-3 py-1.5 bg-white border border-[#E2E8F0] hover:border-blue-300 text-xs font-semibold rounded-xl text-[#172033] transition-colors shadow-xs"
          >
            Standard Scenario
          </button>
          <button
            type="button"
            onClick={() => setFormData(HIGH_RISK_PRESET)}
            className="px-3 py-1.5 bg-rose-50 border border-rose-200 hover:bg-rose-100 text-xs font-semibold rounded-xl text-rose-700 transition-colors shadow-xs"
          >
            Severe Delay Risk
          </button>
          <button
            type="button"
            onClick={() => setFormData(LOW_RISK_PRESET)}
            className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 text-xs font-semibold rounded-xl text-emerald-700 transition-colors shadow-xs"
          >
            Clear / Optimal Route
          </button>
        </div>
      </div>

      {/* Error Message if API fails */}
      {error && (
        <ErrorMessage 
          title="Prediction Request Failed"
          message={error}
          onRetry={handlePredict}
        />
      )}

      {/* Prediction Output Section (renders when result is available) */}
      {result && (
        <PredictionResult result={result} inputRecord={formData} />
      )}

      {/* Multi-Section Telemetry Form */}
      <form onSubmit={handlePredict} className="space-y-6">
        
        {/* SECTION 1: Shipment & Route Telemetry */}
        <SectionCard
          title="1. Shipment & Route Information"
          subtitle="Route distance, travel duration estimates, and live corridor traffic sensors"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Departure Date & Time
              </label>
              <input
                type="datetime-local"
                name="departure_date"
                value={formData.departure_date}
                onChange={handleChange}
                required
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
              <span className="text-[10px] text-[#64748B] mt-1 block">Derives hour, day of week, peak flag</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Route Distance (miles)
              </label>
              <input
                type="number"
                name="distance"
                step="0.1"
                value={formData.distance}
                onChange={handleChange}
                required
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Estimated Transit Hours
              </label>
              <input
                type="number"
                name="average_hours"
                step="0.1"
                value={formData.average_hours}
                onChange={handleChange}
                required
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Corridor Traffic Density (veh/hr)
              </label>
              <input
                type="number"
                name="traffic_vehicles"
                step="1"
                value={formData.traffic_vehicles}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Active Traffic Accident Flag
              </label>
              <select
                name="traffic_accident"
                value={formData.traffic_accident}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all bg-white"
              >
                <option value={0}>0 — Normal Traffic Flow</option>
                <option value={1}>1 — Accident Reported on Route</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Daily Accident Frequency on Segment
              </label>
              <input
                type="number"
                name="daily_accident_count"
                value={formData.daily_accident_count}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

          </div>
        </SectionCard>

        {/* SECTION 2: Truck Specifications */}
        <SectionCard
          title="2. Truck Vehicle Specifications"
          subtitle="Vehicle age, load capacity rating, mileage economy, and fuel classification"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Truck Age (years)
              </label>
              <input
                type="number"
                name="truck_age"
                value={formData.truck_age}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Load Capacity (pounds)
              </label>
              <input
                type="number"
                name="load_capacity_pounds"
                step="500"
                value={formData.load_capacity_pounds}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Fuel Efficiency (MPG)
              </label>
              <input
                type="number"
                name="mileage_mpg"
                step="0.5"
                value={formData.mileage_mpg}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Fuel Type
              </label>
              <select
                name="fuel_type"
                value={formData.fuel_type}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all bg-white"
              >
                <option value="diesel">Diesel</option>
                <option value="gas">Gasoline</option>
                <option value="electric">Electric / Alternative</option>
              </select>
            </div>

          </div>
        </SectionCard>

        {/* SECTION 3: Driver Telemetry */}
        <SectionCard
          title="3. Assigned Driver Information"
          subtitle="Driver tenure, commercial experience, historical performance ratings, and driving style"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Driver Age
              </label>
              <input
                type="number"
                name="driver_age"
                value={formData.driver_age}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Experience (years)
              </label>
              <input
                type="number"
                name="experience"
                value={formData.experience}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Safety Rating (1–10)
              </label>
              <input
                type="number"
                name="driver_ratings"
                min="1"
                max="10"
                step="0.5"
                value={formData.driver_ratings}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Average Speed (MPH)
              </label>
              <input
                type="number"
                name="average_speed_mph"
                step="0.5"
                value={formData.average_speed_mph}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Driving Style
              </label>
              <select
                name="driving_style"
                value={formData.driving_style}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all bg-white"
              >
                <option value="proactive">Proactive</option>
                <option value="conservative">Conservative</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>

          </div>
        </SectionCard>

        {/* SECTION 4: Weather Conditions */}
        <SectionCard
          title="4. Atmospheric & Weather Information"
          subtitle="Recorded corridor meteorological data at departure window"
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Temperature (°C)
              </label>
              <input
                type="number"
                name="weather_temp"
                step="0.5"
                value={formData.weather_temp}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Wind Speed (km/h)
              </label>
              <input
                type="number"
                name="weather_wind_speed"
                step="0.5"
                value={formData.weather_wind_speed}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Precipitation (mm)
              </label>
              <input
                type="number"
                name="weather_precip"
                step="0.1"
                value={formData.weather_precip}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Humidity (%)
              </label>
              <input
                type="number"
                name="weather_humidity"
                value={formData.weather_humidity}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Visibility (km)
              </label>
              <input
                type="number"
                name="weather_visibility"
                value={formData.weather_visibility}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Chance of Rain (%)
              </label>
              <input
                type="number"
                name="weather_chanceofrain"
                value={formData.weather_chanceofrain}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Chance of Fog (%)
              </label>
              <input
                type="number"
                name="weather_chanceoffog"
                value={formData.weather_chanceoffog}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Chance of Snow (%)
              </label>
              <input
                type="number"
                name="weather_chanceofsnow"
                value={formData.weather_chanceofsnow}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Chance of Thunder (%)
              </label>
              <input
                type="number"
                name="weather_chanceofthunder"
                value={formData.weather_chanceofthunder}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

          </div>
        </SectionCard>

        {/* SECTION 5: Historical Baselines */}
        <SectionCard
          title="5. Historical Performance Baselines"
          subtitle="Top predictive indicators identified in XGBoost feature importance analysis"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Truck Historical Delay Rate
              </label>
              <input
                type="number"
                name="truck_delay_rate_hist"
                step="0.01"
                min="0"
                max="1"
                value={formData.truck_delay_rate_hist}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
              <span className="text-[10px] text-[#64748B] mt-1 block">e.g. 0.35 = 35% past late trips</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Truck Trip Count
              </label>
              <input
                type="number"
                name="truck_trip_count_hist"
                value={formData.truck_trip_count_hist}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Route Historical Delay Rate
              </label>
              <input
                type="number"
                name="route_delay_rate_hist"
                step="0.01"
                min="0"
                max="1"
                value={formData.route_delay_rate_hist}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
              <span className="text-[10px] text-[#64748B] mt-1 block">e.g. 0.28 = 28% route late rate</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1.5">
                Route Trip Count
              </label>
              <input
                type="number"
                name="route_trip_count_hist"
                value={formData.route_trip_count_hist}
                onChange={handleChange}
                className="w-full px-3.5 py-2 border border-[#E2E8F0] rounded-xl text-xs focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] outline-none transition-all"
              />
            </div>

          </div>
        </SectionCard>

        {/* Primary Action Button */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs text-[#64748B] flex items-center gap-1.5">
            <Info className="w-4 h-4 text-[#2563EB] shrink-0" />
            <span>Sends JSON payload directly to <code className="text-[#2563EB] font-mono font-semibold">POST /api/delay</code></span>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => setFormData(DEFAULT_FORM)}
              className="px-4 py-3 bg-white border border-[#E2E8F0] hover:bg-slate-50 text-xs font-semibold rounded-xl text-[#172033] transition-colors"
            >
              Reset Defaults
            </button>

            <button
              type="submit"
              disabled={loading}
              className="flex-1 sm:flex-initial px-8 py-3 bg-[#2563EB] hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 min-w-[200px]"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing Shipment...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Predict Delay Probability</span>
                </>
              )}
            </button>
          </div>
        </div>

      </form>
    </div>
  );
}
