export interface Job {
  id: string
  title: string
  company_name: string
  location?: string
  is_remote: boolean
  salary_min?: number
  salary_max?: number
  salary_currency?: string
  seniority_level?: string
  employment_type?: string
  match_score?: number
  rule_score?: number
  embedding_score?: number
  posting_url?: string
  apply_url?: string
  source_type?: string
  description?: string
  created_at?: string
}

export interface DashboardSummary {
  total_jobs: number
  high_matches: number
  applications: number
  interviews: number
  offers: number
}

export interface TimeSeriesPoint {
  date: string
  jobs: number
  matched: number
  applications: number
  interviews: number
  offers: number
}

export interface SkillDemand {
  skill: string
  count: number
}

export interface DashboardData {
  summary: DashboardSummary
  time_series: TimeSeriesPoint[]
  top_skills: SkillDemand[]
}

export interface ApplicationItem {
  id: string
  job_id: string
  job_title: string
  company_name: string
  current_stage: string
  applied_at?: string
  recruiter_name?: string
  next_interview_at?: string
  offer_amount?: number
}

const API_BASE = '/api/v1'

export async function fetchJobs(minScore?: number): Promise<Job[]> {
  const url = minScore ? `${API_BASE}/jobs/?min_score=${minScore}` : `${API_BASE}/jobs/`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch jobs')
  const data = await res.json()
  return data.items || []
}

export async function fetchDashboard(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/analytics/dashboard?days=30`)
  if (!res.ok) throw new Error('Failed to fetch dashboard analytics')
  return res.json()
}

export async function fetchApplications(): Promise<ApplicationItem[]> {
  const res = await fetch(`${API_BASE}/applications/`)
  if (!res.ok) throw new Error('Failed to fetch applications')
  const data = await res.json()
  return data.items || []
}

export async function triggerScrape(keyword: string = 'Software Engineer'): Promise<any> {
  const res = await fetch(`${API_BASE}/scrapers/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title_keyword: keyword, location: 'India' }),
  })
  if (!res.ok) throw new Error('Scrape trigger failed')
  return res.json()
}

export async function generateCoverLetter(jobId: string, resumeVersionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/intelligence/cover-letter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, resume_version_id: resumeVersionId, tone: 'professional' }),
  })
  if (!res.ok) throw new Error('Cover letter generation failed')
  return res.json()
}

export async function generateRecruiterMessage(jobId: string, resumeVersionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/intelligence/recruiter-message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, resume_version_id: resumeVersionId, channel: 'linkedin' }),
  })
  if (!res.ok) throw new Error('Recruiter message generation failed')
  return res.json()
}
