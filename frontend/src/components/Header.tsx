import React from 'react'
import { Download, Play, Briefcase, BarChart3, Layers, FileUp, ShieldCheck } from 'lucide-react'

interface HeaderProps {
  activeTab: 'feed' | 'kanban' | 'analytics'
  setActiveTab: (tab: 'feed' | 'kanban' | 'analytics') => void
  onTriggerScrape: () => void
  isScraping: boolean
  onOpenUploadResume: () => void
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  onTriggerScrape,
  isScraping,
  onOpenUploadResume,
}) => {
  const handleExportExcel = () => {
    window.open('/api/v1/reports/excel', '_blank')
  }

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Clean Professional Brand */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm font-bold text-lg">
            H
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">HuntIQ</h1>
              <span className="text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Enterprise
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Career Intelligence Platform</p>
          </div>
        </div>

        {/* Minimal Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('feed')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-colors ${
              activeTab === 'feed'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Briefcase className="h-3.5 w-3.5" />
            AI Match Feed
          </button>

          <button
            onClick={() => setActiveTab('kanban')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-colors ${
              activeTab === 'kanban'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            Applications
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-colors ${
              activeTab === 'analytics'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Analytics
          </button>
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onOpenUploadResume}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            <FileUp className="h-3.5 w-3.5 text-blue-400" />
            Upload Resume
          </button>

          <button
            onClick={onTriggerScrape}
            disabled={isScraping}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors disabled:opacity-50"
          >
            <Play className={`h-3.5 w-3.5 ${isScraping ? 'animate-spin' : ''}`} />
            {isScraping ? 'Scraping...' : 'Run Scrapers'}
          </button>

          <button
            onClick={handleExportExcel}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-colors"
            title="Download Excel Report"
          >
            <Download className="h-3.5 w-3.5 text-emerald-400" />
            Export Excel
          </button>
        </div>
      </div>
    </header>
  )
}
