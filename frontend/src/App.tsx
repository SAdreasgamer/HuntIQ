import React, { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { MetricCard } from './components/MetricCard'
import { JobFeed } from './components/JobFeed'
import { KanbanBoard } from './components/KanbanBoard'
import { AnalyticsCharts } from './components/AnalyticsCharts'
import { AIInspectorModal } from './components/AIInspectorModal'
import { ResumeUploadModal } from './components/ResumeUploadModal'
import {
  Job,
  DashboardData,
  ApplicationItem,
  fetchJobs,
  fetchDashboard,
  fetchApplications,
  triggerScrape,
} from './api'
import { Briefcase, Award, Send, Users, Trophy } from 'lucide-react'

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'feed' | 'kanban' | 'analytics'>('feed')
  const [jobs, setJobs] = useState<Job[]>([])
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [applications, setApplications] = useState<ApplicationItem[]>([])
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [isScraping, setIsScraping] = useState<boolean>(false)
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false)

  const loadData = async () => {
    try {
      const [jobsData, dashData, appsData] = await Promise.all([
        fetchJobs(),
        fetchDashboard(),
        fetchApplications(),
      ])
      setJobs(jobsData)
      setDashboard(dashData)
      setApplications(appsData)
    } catch (err) {
      console.error('Failed to load backend data:', err)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleTriggerScrape = async () => {
    setIsScraping(true)
    try {
      await triggerScrape('Software Engineer')
      await loadData()
    } catch (err) {
      console.error('Scrape failed:', err)
    } finally {
      setIsScraping(false)
    }
  }

  const summary = dashboard?.summary || {
    total_jobs: jobs.length || 10,
    high_matches: jobs.filter((j) => (j.match_score || 0) >= 80).length || 2,
    applications: applications.length || 0,
    interviews: 0,
    offers: 0,
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Header Bar */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onTriggerScrape={handleTriggerScrape}
        isScraping={isScraping}
        onOpenUploadResume={() => setIsUploadOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-5 space-y-5">
        {/* Top KPI Cards Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          <MetricCard
            title="Total Discovered"
            value={summary.total_jobs}
            subtitle="Active job listings"
            icon={Briefcase}
            color="blue"
          />
          <MetricCard
            title="High AI Matches"
            value={summary.high_matches}
            subtitle=">= 80% match score"
            icon={Award}
            color="emerald"
          />
          <MetricCard
            title="Applications"
            value={summary.applications}
            subtitle="Active pipeline"
            icon={Send}
            color="blue"
          />
          <MetricCard
            title="Interviews"
            value={summary.interviews}
            subtitle="Scheduled rounds"
            icon={Users}
            color="amber"
          />
          <MetricCard
            title="Job Offers"
            value={summary.offers}
            subtitle="Offer negotiations"
            icon={Trophy}
            color="emerald"
          />
        </div>

        {/* Dynamic Tab Views */}
        {activeTab === 'feed' && <JobFeed jobs={jobs} onInspectJob={(job) => setSelectedJob(job)} />}

        {activeTab === 'kanban' && <KanbanBoard applications={applications} />}

        {activeTab === 'analytics' && dashboard && <AnalyticsCharts data={dashboard} />}
      </main>

      {/* AI Inspector Modal */}
      <AIInspectorModal job={selectedJob} onClose={() => setSelectedJob(null)} />

      {/* Resume Upload Modal */}
      <ResumeUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={() => {
          loadData()
        }}
      />
    </div>
  )
}

export default App
