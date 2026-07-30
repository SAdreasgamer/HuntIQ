import React, { useState } from 'react'
import { Job } from '../api'
import { MapPin, Globe, Sparkles, ExternalLink } from 'lucide-react'

interface JobFeedProps {
  jobs: Job[]
  onInspectJob: (job: Job) => void
}

export const JobFeed: React.FC<JobFeedProps> = ({ jobs, onInspectJob }) => {
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0)

  const filteredJobs = jobs.filter((j) => (j.match_score || 0) >= minScoreFilter)

  return (
    <div className="space-y-4">
      {/* Clean Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pro-card p-3.5">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-300">Filter by Composite Match:</span>
          <div className="flex gap-1.5">
            {[0, 60, 75, 85].map((score) => (
              <button
                key={score}
                onClick={() => setMinScoreFilter(score)}
                className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                  minScoreFilter === score
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
                }`}
              >
                {score === 0 ? 'All Jobs' : `>= ${score}%`}
              </button>
            ))}
          </div>
        </div>

        <span className="text-xs text-slate-400">
          Showing <span className="text-slate-200 font-semibold">{filteredJobs.length}</span> active listings
        </span>
      </div>

      {/* Clean Jobs List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {filteredJobs.map((job) => {
          const matchScore = roundScore(job.match_score)

          return (
            <div
              key={job.id}
              className="pro-card pro-card-hover p-4 flex flex-col justify-between"
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-base font-bold text-slate-100 line-clamp-1">
                      {job.title}
                    </h4>
                    <p className="text-xs font-medium text-slate-400 mt-0.5">{job.company_name}</p>
                  </div>

                  {/* Clean Match Badge */}
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-bold ${
                      matchScore >= 85
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : matchScore >= 70
                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    {matchScore}% Match
                  </span>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap items-center gap-2 mt-3">
                  {job.location && (
                    <span className="flex items-center gap-1 text-[11px] text-slate-400 bg-slate-800/80 px-2.5 py-0.5 rounded border border-slate-700/60">
                      <MapPin className="h-3 w-3 text-slate-400" />
                      {job.location}
                    </span>
                  )}
                  {job.is_remote && (
                    <span className="flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">
                      <Globe className="h-3 w-3" />
                      Remote
                    </span>
                  )}
                  {job.salary_max && (
                    <span className="text-[11px] font-semibold text-slate-300 bg-slate-800 px-2.5 py-0.5 rounded border border-slate-700">
                      ${(job.salary_max / 1000).toFixed(0)}k Max
                    </span>
                  )}
                </div>

                {/* Sub Score Breakdown */}
                <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
                  <div>
                    Rule Score: <span className="font-semibold text-slate-200">{roundScore(job.rule_score)}%</span>
                  </div>
                  <div>
                    Semantic Similarity: <span className="font-semibold text-slate-200">{roundScore(job.embedding_score)}%</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between gap-2 mt-4 pt-3 border-t border-slate-800">
                <button
                  onClick={() => onInspectJob(job)}
                  className="flex items-center gap-1.5 px-3 py-1 rounded bg-blue-600/10 text-blue-400 hover:bg-blue-600 hover:text-white border border-blue-500/30 text-xs font-semibold transition-colors"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  AI Intelligence & Outreach
                </button>

                {job.posting_url && (
                  <a
                    href={job.posting_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    Listing
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
