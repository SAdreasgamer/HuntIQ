import React from 'react'
import { DashboardData } from '../api'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts'

interface AnalyticsChartsProps {
  data: DashboardData
}

export const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ data }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Time-Series Area Chart */}
      <div className="glass-card p-5 rounded-2xl border border-slate-800">
        <h4 className="text-base font-bold text-white mb-4">Job Search Performance History</h4>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.time_series}>
              <defs>
                <linearGradient id="jobsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="matchedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '12px',
                  color: '#f8fafc',
                }}
              />
              <Area
                type="monotone"
                dataKey="jobs"
                name="Total Jobs"
                stroke="#6366f1"
                fillOpacity={1}
                fill="url(#jobsGrad)"
              />
              <Area
                type="monotone"
                dataKey="matched"
                name="High Matches"
                stroke="#10b981"
                fillOpacity={1}
                fill="url(#matchedGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Skills Demand Bar Chart */}
      <div className="glass-card p-5 rounded-2xl border border-slate-800">
        <h4 className="text-base font-bold text-white mb-4">Top Demanded Tech Stack Skills</h4>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.top_skills.slice(0, 8)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="skill" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '12px',
                  color: '#f8fafc',
                }}
              />
              <Bar dataKey="count" name="Job Postings Count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
