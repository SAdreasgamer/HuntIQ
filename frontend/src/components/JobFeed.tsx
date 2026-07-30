import React, { useState } from 'react'
import { Job } from '../api'
import { MapPin, Globe, Sparkles, FileText, Send, ExternalLink, Award } from 'lucide-react'

interface JobFeedProps {
  jobs: Job[]
  onInspectJob: (job: Job) => void
}

export const JobFeed: React.FC<JobFeedProps> = ({ jobs, onInspectJob }) => {
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0)

  const filteredJobs = jobs.filter((j) => (j.match_score || 0) >= minScoreFilter)

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 glass-card p-4 rounded-xl">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-slate-300">Filter by Composite Match %:</span>
          <div className="flex gap-2">
            {[0, 60, 75, 85].map((score) => (
              <button
                key={score}
                onClick={() => setMinScoreFilter(score)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  minScoreFilter === score
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {score === 0 ? 'All Jobs' : `>= ${score}% Match`}
              </button>
            ))}
          </div>
        </div>

        <span className="text-xs text-slate-400 font-medium">
          Showing <span className="text-indigo-400 font-bold">{filteredJobs.length}</span> opportunity postings
        </span>
      </div>

      {/* Jobs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredJobs.map((job) => {
          const matchScore = roundScore(job.match_score)
          const isHighMatch = matchScore >= 80

          return (
            <div
              key={job.id}
              className={`glass-card glass-card-hover p-5 rounded-2xl border transition-all flex flex-col justify-between ${
                isHighMatch ? 'border-emerald-500/30 bg-emerald-950/10' : 'border-slate-800'
              }`}
            >
              <div>
                {/* Card Header */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors line-clamp-1">
                      {job.title}
                    </h4>
                    <p className="text-sm font-medium text-slate-400">{job.company_name}</p>
                  </div>

                  {/* Match Score Pill */}
                  <div
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold shadow-sm ${
                      matchScore >= 85
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : matchScore >= 70
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    <Award className="h-3.5 w-3.5" />
                    {matchScore}% AI Match
                  </div>
                </div>

                {/* Tags & Meta */}
                <div className="flex flex-wrap items-center gap-2 mt-3">
                  {job.location && (
                    <span className="flex items-center gap-1 text-xs text-slate-400 bg-slate-900/80 px-2.5 py-1 rounded-lg border border-slate-800">
                      <MapPin className="h-3 w-3 text-indigo-400" />
                      {job.location}
                    </span>
                  )}
                  {job.is_remote && (
                    <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                      <Globe className="h-3 w-3" />
                      Remote
                    </span>
                  )}
                  {job.salary_max && (
                    <span className="text-xs font-semibold text-amber-300 bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20">
                      ${(job.salary_max / 1000).toFixed(0)}k Max
                    </span>
                  )}
                </div>

                {/* Sub-Scores */}
                <div className="grid grid-cols-2 gap-2 mt-4 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs">
                  <div>
                    <span className="text-slate-500">Rule Match:</span>{' '}
                    <span className="font-semibold text-slate-300">{roundScore(job.rule_score)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Semantic Sim:</span>{' '}
                    <span className="font-semibold text-slate-300">{roundScore(job.embedding_score)}%</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between gap-2 mt-5 pt-3 border-t border-slate-800/80">
                <button
                  onClick={() => onInspectJob(job)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold hover:bg-indigo-600 hover:text-white transition-all shadow-sm"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  AI Intelligence & Outreach
                </button>

                {job.posting_url && (
                  <a
                    href={job.posting_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
                  >
                    View Listing
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function roundScore(score?: number): number {
  return score ? Math.round(score) : 0
}
