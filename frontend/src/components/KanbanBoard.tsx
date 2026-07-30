import React from 'react'
import { ApplicationItem } from '../api'
import { Bookmark, Send, PhoneCall, Code2, Users, Trophy } from 'lucide-react'

interface KanbanBoardProps {
  applications: ApplicationItem[]
}

const STAGES = [
  { id: 'bookmarked', label: 'Bookmarked', icon: Bookmark },
  { id: 'applied', label: 'Applied', icon: Send },
  { id: 'screening', label: 'Screening', icon: PhoneCall },
  { id: 'technical', label: 'Technical', icon: Code2 },
  { id: 'interview', label: 'Interview', icon: Users },
  { id: 'offer', label: 'Offer', icon: Trophy },
]

export const KanbanBoard: React.FC<KanbanBoardProps> = ({ applications }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3.5 overflow-x-auto pb-4">
      {STAGES.map((stage) => {
        const Icon = stage.icon
        const items = applications.filter((a) => a.current_stage.toLowerCase() === stage.id)

        return (
          <div key={stage.id} className="pro-card p-3 flex flex-col min-w-[230px]">
            {/* Column Header */}
            <div className="flex items-center justify-between p-2 rounded bg-slate-800/80 border border-slate-700/60 mb-3">
              <div className="flex items-center gap-2">
                <Icon className="h-3.5 w-3.5 text-blue-400" />
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">{stage.label}</h4>
              </div>
              <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-slate-900 text-slate-300">
                {items.length}
              </span>
            </div>

            {/* Application Cards */}
            <div className="flex-1 space-y-2 overflow-y-auto max-h-[600px]">
              {items.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-500 italic border border-dashed border-slate-800 rounded">
                  No items
                </div>
              ) : (
                items.map((app) => (
                  <div
                    key={app.id}
                    className="p-3 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors"
                  >
                    <h5 className="text-xs font-bold text-slate-100 line-clamp-1">{app.job_title}</h5>
                    <p className="text-[11px] text-slate-400 mt-0.5">{app.company_name}</p>

                    {app.recruiter_name && (
                      <p className="text-[10px] text-slate-500 mt-1.5">
                        Recruiter: <span className="text-slate-300">{app.recruiter_name}</span>
                      </p>
                    )}

                    {app.offer_amount && (
                      <div className="mt-2 text-xs font-bold text-emerald-400 bg-emerald-500/10 p-1 rounded border border-emerald-500/20 text-center">
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
