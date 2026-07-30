import React from 'react'
import { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: number | string
  subtitle?: string
  icon: LucideIcon
  color?: 'blue' | 'emerald' | 'amber' | 'slate'
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
}) => {
  return (
    <div className="pro-card p-4 flex items-center justify-between">
      <div>
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">{title}</p>
        <h3 className="text-2xl font-bold text-slate-900 mt-1">{value}</h3>
        {subtitle && <p className="text-[11px] text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-100 text-blue-600">
        <Icon className="h-5 w-5" />
      </div>
    </div>
  )
}
