import React from 'react'
import { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: number | string
  subtitle?: string
  icon: LucideIcon
  color: 'indigo' | 'emerald' | 'amber' | 'cyan' | 'purple'
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}) => {
  const colorStyles = {
    indigo: 'from-indigo-500/20 to-indigo-600/5 text-indigo-400 border-indigo-500/30 icon-bg:bg-indigo-500/20',
    emerald: 'from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/30 icon-bg:bg-emerald-500/20',
    amber: 'from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/30 icon-bg:bg-amber-500/20',
    cyan: 'from-cyan-500/20 to-cyan-600/5 text-cyan-400 border-cyan-500/30 icon-bg:bg-cyan-500/20',
    purple: 'from-purple-500/20 to-purple-600/5 text-purple-400 border-purple-500/30 icon-bg:bg-purple-500/20',
  }

  return (
    <div className={`glass-card glass-card-hover bg-gradient-to-br ${colorStyles[color]} p-5 rounded-2xl border`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
          <h3 className="text-3xl font-extrabold text-white mt-1">{value}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        </div>
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  )
}
