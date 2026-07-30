import React from 'react'
import { ApplicationItem } from '../api'
import { Bookmark, Send, PhoneCall, Code2, Users, Trophy, ChevronRight } from 'lucide-react'

interface KanbanBoardProps {
  applications: ApplicationItem[]
}

const STAGES = [
  { id: 'bookmarked', label: 'Bookmarked', icon: Bookmark, color: 'border-slate-700 bg-slate-900/40 text-slate-400' },
  { id: 'applied', label: 'Applied', icon: Send, color: 'border-indigo-500/30 bg-indigo-950/20 text-indigo-400' },
  { id: 'screening', label: 'Screening', icon: PhoneCall, color: 'border-cyan-500/30 bg-cyan-950/20 text-cyan-400' },
  { id: 'technical', label: 'Technical', icon: Code2, color: 'border-amber-500/30 bg-amber-950/20 text-amber-400' },
  { id: 'interview', label: 'Interview', icon: Users, color: 'border-purple-500/30 bg-purple-950/20 text-purple-400' },
  { id: 'offer', label: 'Offer', icon: Trophy, color: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-400' },
]

export const KanbanBoard: React.FC<KanbanBoardProps> = ({ applications }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 overflow-x-auto pb-4">
      {STAGES.map((stage) => {
        const Icon = stage.icon
        const items = applications.filter((a) => a.current_stage.toLowerCase() === stage.id)

        return (
          <div key={stage.id} className="flex flex-col glass-card rounded-2xl p-3 min-w-[240px]">
            {/* Column Header */}
            <div className={`flex items-center justify-between p-2.5 rounded-xl border mb-3 ${stage.color}`}>
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider">{stage.label}</h4>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-slate-900/80 border border-slate-800">
                {items.length}
              </span>
            </div>

            {/* Application Cards */}
            <div className="flex-1 space-y-3 overflow-y-auto max-h-[600px] pr-1">
              {items.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500 italic border border-dashed border-slate-800/80 rounded-xl">
                  No applications
                </div>
              ) : (
                items.map((app) => (
                  <div
                    key={app.id}
                    className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-indigo-500/40 transition-all shadow-sm"
                  >
                    <h5 className="text-sm font-semibold text-white line-clamp-1">{app.job_title}</h5>
                    <p className="text-xs text-slate-400 mt-0.5">{app.company_name}</p>

                    {app.recruiter_name && (
                      <p className="text-[11px] text-slate-500 mt-2">
                        Recruiter: <span className="text-slate-300">{app.recruiter_name}</span>
                      </p>
                    )}

                    {app.offer_amount && (
                      <div className="mt-2 text-xs font-bold text-emerald-400 bg-emerald-500/10 p-1.5 rounded-lg border border-emerald-500/20 text-center">
                        Offer: ${app.offer_amount.toLocaleString()}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
