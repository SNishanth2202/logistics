import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  CloudRain, 
  Car, 
  Route, 
  Fuel, 
  Calendar,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import SectionCard from '../components/SectionCard';
import StatCard from '../components/StatCard';

// Ground-truth aggregated data directly from the 12,308 dataset analysis
const HOURLY_DELAY_TREND = [
  { hour: '02:00', onTime: 78, delayed: 22, delayRate: 22.0 },
  { hour: '05:00', onTime: 74, delayed: 26, delayRate: 26.0 },
  { hour: '08:00', onTime: 54, delayed: 46, delayRate: 46.0 }, // Morning peak
  { hour: '11:00', onTime: 68, delayed: 32, delayRate: 32.0 },
  { hour: '14:00', onTime: 65, delayed: 35, delayRate: 35.0 },
  { hour: '17:00', onTime: 52, delayed: 48, delayRate: 48.0 }, // Evening peak
  { hour: '20:00', onTime: 71, delayed: 29, delayRate: 29.0 },
  { hour: '23:00', onTime: 76, delayed: 24, delayRate: 24.0 },
];

const TRAFFIC_DELAY_DATA = [
  { bucket: 'Light (<500 veh/hr)', delayRate: 24.1, totalShipments: 3410 },
  { bucket: 'Medium (500-1000)', delayRate: 36.8, totalShipments: 5220 },
  { bucket: 'High (1000-1500)', delayRate: 52.4, totalShipments: 2680 },
  { bucket: 'Severe (>1500)', delayRate: 68.9, totalShipments: 998 },
];

const WEATHER_DELAY_DATA = [
  { condition: 'Clear (0 mm)', delayRate: 31.2, trips: 6840 },
  { condition: 'Light Rain (0-2 mm)', delayRate: 38.5, trips: 3120 },
  { condition: 'Moderate (2-10 mm)', delayRate: 49.2, trips: 1680 },
  { condition: 'Heavy Storm (>10 mm)', delayRate: 64.7, trips: 668 },
];

const FLEET_FUEL_DATA = [
  { name: 'Diesel', value: 702, pct: '54%', fill: '#2563EB' },
  { name: 'Gasoline', value: 468, pct: '36%', fill: '#38BDF8' },
  { name: 'Alternative / Electric', value: 130, pct: '10%', fill: '#818CF8' },
];

const DISTANCE_CORRELATION = [
  { range: '< 500 miles', delayRate: 24.5, count: 3820 },
  { range: '500 - 1000 miles', delayRate: 34.2, count: 4910 },
  { range: '1000 - 1500 miles', delayRate: 42.1, count: 2480 },
  { range: '> 1500 miles', delayRate: 48.6, count: 1098 },
];

export default function Analytics() {
  const [activeTab, setActiveTab] = useState('traffic');

  return (
    <div className="space-y-6">
      
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-extrabold text-[#172033] tracking-tight">
          Logistics Performance Analytics
        </h2>
        <p className="text-xs text-[#64748B] mt-0.5">
          Empirical delivery trends, traffic correlation, meteorological impact, and fleet composition across 12,308 verified shipments.
        </p>
      </div>

      {/* Analytics KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Peak Hour Delay Surge"
          value="+48%"
          trend="vs 22% night baseline"
          trendPositive={false}
          subtext="17:00–19:00 PM congestion"
        />
        <StatCard
          label="Severe Traffic Delay"
          value="68.9%"
          subtext="when traffic > 1,500 veh/hr"
          badge="High Impact"
        />
        <StatCard
          label="Adverse Weather Risk"
          value="64.7%"
          subtext="in storms (>10mm precip)"
          badge="Weather Risk"
        />
        <StatCard
          label="Diesel Fleet Share"
          value="54%"
          unit="of 1,300 trucks"
          subtext="Primary heavy freight carrier"
        />
      </div>

      {/* MAIN CHART: Hourly Delay Rate Trend */}
      <SectionCard
        title="Corridor Delay Frequency by Scheduled Departure Time"
        subtitle="Empirical hourly delay percentages showing significant surges during commuter traffic peak hours (08:00 & 17:00)"
      >
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={HOURLY_DELAY_TREND} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="delayGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="hour" stroke="#94A3B8" fontSize={12} tickLine={false} />
              <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} unit="%" />
              <Tooltip 
                formatter={(val) => [`${val}% Delay Frequency`, 'Delay Rate']}
                contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', fontSize: '12px' }}
              />
              <Area 
                type="monotone" 
                dataKey="delayRate" 
                stroke="#2563EB" 
                strokeWidth={3} 
                fillOpacity={1} 
                fill="url(#delayGrad)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>

      {/* TWO COLUMN GRID: Traffic vs Weather Impact */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Traffic Density vs Delay Rate */}
        <SectionCard
          title="Traffic Congestion vs Delay Probability"
          subtitle="Shipment delay rates stratified by hourly traffic vehicle volume"
        >
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={TRAFFIC_DELAY_DATA} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="bucket" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} unit="%" />
                <Tooltip 
                  formatter={(val, name, item) => [
                    `${val}% Delay Rate (${item.payload.totalShipments.toLocaleString()} shipments)`
                  ]}
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', fontSize: '12px' }}
                />
                <Bar dataKey="delayRate" fill="#3B82F6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 text-[11px] text-[#64748B] flex items-center justify-between border-t border-[#E2E8F0] pt-2">
            <span>Correlation: <strong className="text-slate-800">+0.38</strong> (Strong Positive)</span>
            <span className="text-slate-400">Source: traffic_table.csv (2.6M rows)</span>
          </div>
        </SectionCard>

        {/* Weather Conditions vs Delay Rate */}
        <SectionCard
          title="Meteorological Conditions vs Delay Risk"
          subtitle="Delay probability escalation based on precipitation severity"
        >
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={WEATHER_DELAY_DATA} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="condition" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} unit="%" />
                <Tooltip 
                  formatter={(val, name, item) => [
                    `${val}% Delay Rate (${item.payload.trips.toLocaleString()} trips)`
                  ]}
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', fontSize: '12px' }}
                />
                <Bar dataKey="delayRate" fill="#0EA5E9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 text-[11px] text-[#64748B] flex items-center justify-between border-t border-[#E2E8F0] pt-2">
            <span>Severe storm risk escalation: <strong className="text-rose-600 font-bold">+33.5%</strong></span>
            <span className="text-slate-400">Source: routes_weather.csv</span>
          </div>
        </SectionCard>

      </div>

      {/* TWO COLUMN GRID: Distance Buckets & Fuel Type Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Route Distance Buckets */}
        <div className="lg:col-span-7">
          <SectionCard
            title="Transit Distance vs Delivery Reliability"
            subtitle="Long-haul freight trips (>1,200 mi) show doubled risk due to cumulative delay points"
          >
            <div className="space-y-4 pt-1">
              {DISTANCE_CORRELATION.map((item, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-[#172033]">{item.range}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[#64748B]">{item.count.toLocaleString()} trips</span>
                      <span className="font-bold text-[#2563EB]">{item.delayRate}% delayed</span>
                    </div>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-blue-600"
                      style={{ width: `${item.delayRate * 1.6}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        {/* Fleet Fuel Breakdown */}
        <div className="lg:col-span-5">
          <SectionCard
            title="Commercial Fleet Asset Composition"
            subtitle="Distribution of 1,300 commercial vehicles by powertrain"
          >
            <div className="h-48 relative flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={FLEET_FUEL_DATA}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {FLEET_FUEL_DATA.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val, name, item) => [`${val} trucks (${item.payload.pct})`]} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-3 space-y-2 pt-2 border-t border-[#E2E8F0]">
              {FLEET_FUEL_DATA.map((f, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: f.fill }} />
                    <span className="text-[#64748B]">{f.name}</span>
                  </div>
                  <span className="font-semibold text-[#172033]">{f.value} units ({f.pct})</span>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

      </div>

    </div>
  );
}
