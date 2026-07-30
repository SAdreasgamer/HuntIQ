import React, { useState } from 'react'
import { Job } from '../api'
import { MapPin, Globe, Sparkles, ExternalLink, Briefcase, Clock } from 'lucide-react'

interface JobFeedProps {
  jobs: Job[]
  onInspectJob: (job: Job) => void
}

const SOURCE_COLORS: Record<string, string> = {
  linkedin: '#0A66C2',
  indeed: '#2557A7',
  glassdoor: '#0CAA41',
  naukri: '#4A90D9',
  wellfound: '#000000',
  monster: '#6E45A5',
  remoteok: '#16A34A',
  all_jobs: '#6366F1',
}

function formatSalary(min?: number, max?: number, currency?: string): string {
  if (!min && !max) return ''
  const curr = currency || 'INR'

  const formatNum = (n: number): string => {
    if (curr === 'INR') {
      if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`
      if (n >= 1000) return `₹${(n / 1000).toFixed(0)}K`
      return `₹${n}`
    }
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`
    return `$${n}`
  }

  if (min && max) return `${formatNum(min)} – ${formatNum(max)}`
  if (min) return `${formatNum(min)}+`
  if (max) return `Up to ${formatNum(max)}`
  return ''
}

function timeAgo(dateStr?: string): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return '1d ago'
  if (days < 30) return `${days}d ago`
  return `${Math.floor(days / 30)}mo ago`
}

export const JobFeed: React.FC<JobFeedProps> = ({ jobs, onInspectJob }) => {
  const [filter, setFilter] = useState<'all' | 'high' | 'remote'>('all')

  const filtered = jobs.filter((job) => {
    if (filter === 'high') return (job.match_score ?? 0) >= 70
    if (filter === 'remote') return job.is_remote
    return true
  })

  return (
    <div>
      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {(['all', 'high', 'remote'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '6px 16px',
              borderRadius: '8px',
              border: filter === f ? '1.5px solid #2563EB' : '1px solid #e2e8f0',
              background: filter === f ? '#EFF6FF' : '#ffffff',
              color: filter === f ? '#1D4ED8' : '#64748b',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {f === 'all' ? `All (${jobs.length})` :
             f === 'high' ? `High Match (${jobs.filter(j => (j.match_score ?? 0) >= 70).length})` :
             `Remote (${jobs.filter(j => j.is_remote).length})`}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          color: '#94a3b8',
          fontSize: '15px',
        }}>
          No jobs found. Click "Run Scrapers" to fetch latest openings from 39+ platforms.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filtered.map((job) => {
            const matchScore = job.match_score ?? 0
            const scoreColor =
              matchScore >= 80 ? '#16A34A' :
              matchScore >= 60 ? '#2563EB' :
              matchScore >= 40 ? '#F59E0B' : '#94a3b8'
            const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency)
            const sourceColor = SOURCE_COLORS[job.source_type || ''] || '#6366F1'

            return (
              <div
                key={job.id}
                style={{
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  padding: '20px 24px',
                  transition: 'box-shadow 0.2s ease, border-color 0.2s ease',
                  cursor: 'default',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.06)'
                  e.currentTarget.style.borderColor = '#cbd5e1'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none'
                  e.currentTarget.style.borderColor = '#e2e8f0'
                }}
              >
                {/* Top Row: Title + Score */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {/* Job Title — Clickable Link */}
                    <a
                      href={job.posting_url || job.apply_url || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        fontSize: '16px',
                        fontWeight: 600,
                        color: '#0f172a',
                        textDecoration: 'none',
                        lineHeight: 1.3,
                        display: 'inline-block',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = '#2563EB' }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = '#0f172a' }}
                    >
                      {job.title}
                      {(job.posting_url || job.apply_url) && (
                        <ExternalLink size={13} style={{ marginLeft: '6px', verticalAlign: 'middle', opacity: 0.5 }} />
                      )}
                    </a>

                    {/* Company Name */}
                    <div style={{ fontSize: '14px', color: '#475569', marginTop: '4px', fontWeight: 500 }}>
                      {job.company_name}
                    </div>
                  </div>

                  {/* Match Score Badge */}
                  {matchScore > 0 && (
                    <div style={{
                      background: `${scoreColor}12`,
                      color: scoreColor,
                      padding: '4px 12px',
                      borderRadius: '20px',
                      fontWeight: 700,
                      fontSize: '14px',
                      whiteSpace: 'nowrap',
                      border: `1px solid ${scoreColor}30`,
                    }}>
                      {matchScore.toFixed(0)}% match
                    </div>
                  )}
                </div>

                {/* Meta Row: Location, Salary, Type, Time */}
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '12px',
                  marginTop: '12px',
                  fontSize: '13px',
                  color: '#64748b',
                  alignItems: 'center',
                }}>
                  {job.location && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={13} />
                      {job.location}
                    </span>
                  )}
                  {job.is_remote && (
                    <span style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: '#16A34A',
                      fontWeight: 500,
                    }}>
                      <Globe size={13} />
                      Remote
                    </span>
                  )}
                  {salary && (
                    <span style={{ fontWeight: 500, color: '#475569' }}>{salary}</span>
                  )}
                  {job.seniority_level && (
                    <span style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      textTransform: 'capitalize',
                    }}>
                      <Briefcase size={13} />
                      {job.seniority_level}
                    </span>
                  )}
                  {job.created_at && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={13} />
                      {timeAgo(job.created_at)}
                    </span>
                  )}
                </div>

                {/* Description Snippet */}
                {job.description && (
                  <div style={{
                    marginTop: '10px',
                    fontSize: '13px',
                    color: '#64748b',
                    lineHeight: 1.5,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                  }}>
                    {job.description}
                  </div>
                )}

                {/* Bottom Row: Source Badge + Actions */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '14px',
                  paddingTop: '12px',
                  borderTop: '1px solid #f1f5f9',
                }}>
                  {/* Source Platform Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {job.source_type && (
                      <span style={{
                        background: `${sourceColor}15`,
                        color: sourceColor,
                        padding: '2px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 600,
                        textTransform: 'capitalize',
                        letterSpacing: '0.02em',
                      }}>
                        {job.source_type === 'all_jobs' ? 'Multi-platform' : job.source_type}
                      </span>
                    )}
                    {job.employment_type && (
                      <span style={{
                        background: '#f1f5f9',
                        color: '#64748b',
                        padding: '2px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 500,
                        textTransform: 'capitalize',
                      }}>
                        {job.employment_type}
                      </span>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button
                      onClick={() => onInspectJob(job)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '6px 14px',
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        background: '#ffffff',
                        color: '#475569',
                        fontSize: '12px',
                        fontWeight: 500,
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#f8fafc'
                        e.currentTarget.style.borderColor = '#cbd5e1'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#ffffff'
                        e.currentTarget.style.borderColor = '#e2e8f0'
                      }}
                    >
                      <Sparkles size={13} />
                      AI Inspect
                    </button>

                    {/* Apply Now — Only show if there's a real URL */}
                    {(job.apply_url || job.posting_url) && (
                      <a
                        href={job.apply_url || job.posting_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '6px 16px',
                          borderRadius: '8px',
                          border: 'none',
                          background: '#2563EB',
                          color: '#ffffff',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          textDecoration: 'none',
                          transition: 'all 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#1D4ED8'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#2563EB'
                        }}
                      >
                        Apply Now
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
