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
          <div key={stage.id} className="pro-card p-3 flex flex-col min-w-[230px] bg-slate-50/50">
            {/* Column Header */}
            <div className="flex items-center justify-between p-2 rounded bg-white border border-slate-200 shadow-xs mb-3">
              <div className="flex items-center gap-2">
                <Icon className="h-3.5 w-3.5 text-blue-600" />
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">{stage.label}</h4>
              </div>
              <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                {items.length}
              </span>
            </div>

            {/* Application Cards */}
            <div className="flex-1 space-y-2 overflow-y-auto max-h-[600px]">
              {items.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-400 italic border border-dashed border-slate-200 rounded bg-white">
                  No items
                </div>
              ) : (
                items.map((app) => (
                  <div
                    key={app.id}
                    className="p-3 rounded bg-white border border-slate-200 hover:border-slate-300 transition-colors shadow-xs"
                  >
                    <h5 className="text-xs font-bold text-slate-900 line-clamp-1">{app.job_title}</h5>
                    <p className="text-[11px] text-slate-500 mt-0.5">{app.company_name}</p>

                    {app.recruiter_name && (
                      <p className="text-[10px] text-slate-500 mt-1.5">
                        Recruiter: <span className="text-slate-700">{app.recruiter_name}</span>
                      </p>
                    )}

                    {app.offer_amount && (
                      <div className="mt-2 text-xs font-bold text-emerald-700 bg-emerald-50 p-1 rounded border border-emerald-200 text-center">
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
