import React from 'react'
import { Sparkles, Download, Bell, Play, Briefcase, BarChart3, Layers, FileText } from 'lucide-react'

interface HeaderProps {
  activeTab: 'feed' | 'kanban' | 'analytics'
  setActiveTab: (tab: 'feed' | 'kanban' | 'analytics') => void
  onTriggerScrape: () => void
  isScraping: boolean
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  onTriggerScrape,
  isScraping,
}) => {
  const handleExportExcel = () => {
    window.open('/api/v1/reports/excel', '_blank')
  }

  return (
    <header className="sticky top-0 z-40 glass-card border-b border-slate-800/80 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Sparkles className="h-5 w-5 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
              HuntIQ <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">PRO</span>
            </h1>
            <p className="text-xs text-slate-400">Autonomous AI Job Search Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('feed')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'feed'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Briefcase className="h-4 w-4" />
            AI Match Feed
          </button>

          <button
            onClick={() => setActiveTab('kanban')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'kanban'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Layers className="h-4 w-4" />
            Application Kanban
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'analytics'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            Analytics & Reports
          </button>
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={onTriggerScrape}
            disabled={isScraping}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 text-white text-sm font-semibold shadow-lg shadow-emerald-600/20 hover:from-emerald-500 hover:to-teal-400 transition-all disabled:opacity-50"
          >
            <Play className={`h-4 w-4 ${isScraping ? 'animate-spin' : ''}`} />
            {isScraping ? 'Scraping...' : 'Run Scrapers'}
          </button>

          <button
            onClick={handleExportExcel}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 text-sm font-semibold hover:border-slate-500 hover:bg-slate-800 transition-all shadow-sm"
            title="Download Multi-Sheet Excel Workbook"
          >
            <Download className="h-4 w-4 text-emerald-400" />
            Excel Report
          </button>

          <button className="relative p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-all">
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-indigo-500 animate-ping"></span>
          </button>
        </div>
      </div>
    </header>
  )
}
