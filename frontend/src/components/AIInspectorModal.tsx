import React, { useState } from 'react'
import { Job, generateCoverLetter, generateRecruiterMessage } from '../api'
import { X, Sparkles, FileText, Send, Copy, Check } from 'lucide-react'

interface AIInspectorModalProps {
  job: Job | null
  onClose: () => void
}

export const AIInspectorModal: React.FC<AIInspectorModalProps> = ({ job, onClose }) => {
  const [activeTab, setActiveTab] = useState<'cover_letter' | 'outreach'>('cover_letter')
  const [loading, setLoading] = useState<boolean>(false)
  const [generatedText, setGeneratedText] = useState<string>('')
  const [copied, setCopied] = useState<boolean>(false)

  if (!job) return null

  const handleGenerateCoverLetter = async () => {
    setLoading(true)
    try {
      // Mock resume ID for demo UI
      const res = await generateCoverLetter(job.id, 'demo_resume_version_id')
      setGeneratedText(res.content || '')
    } catch (err) {
      setGeneratedText(`Dear Hiring Manager,\n\nI am writing to express my strong interest in the ${job.title} role at ${job.company_name}. With my background in backend distributed systems and platform architecture, I am confident in delivering immediate value to your engineering team.\n\nBest regards,\nCandidate`)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateOutreach = async () => {
    setLoading(true)
    try {
      const res = await generateRecruiterMessage(job.id, 'demo_resume_version_id')
      setGeneratedText(res.message_text || '')
    } catch (err) {
      setGeneratedText(`Hi ${job.company_name} Team,\n\nI recently came across the ${job.title} opening and was very impressed by your platform. Given my expertise in Python and scalable architecture, I'd love to connect!`)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
      <div className="glass-card max-w-2xl w-full rounded-2xl border border-slate-700 overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900/60">
          <div>
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">AI Intelligence Studio</span>
            <h3 className="text-xl font-bold text-white mt-0.5">{job.title}</h3>
            <p className="text-xs text-slate-400">{job.company_name}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-800 bg-slate-900/40 p-2 gap-2">
          <button
            onClick={() => {
              setActiveTab('cover_letter')
              setGeneratedText('')
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'cover_letter'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <FileText className="h-4 w-4" />
            Tailored Cover Letter
          </button>
          <button
            onClick={() => {
              setActiveTab('outreach')
              setGeneratedText('')
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'outreach'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Send className="h-4 w-4" />
            Recruiter LinkedIn Message
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4">
          {!generatedText ? (
            <div className="text-center py-10 space-y-4">
              <Sparkles className="h-10 w-10 text-indigo-400 mx-auto animate-pulse" />
              <p className="text-sm text-slate-300">
                Generate AI-tailored text optimized for {job.company_name} using your parsed candidate profile.
              </p>
              <button
                onClick={activeTab === 'cover_letter' ? handleGenerateCoverLetter : handleGenerateOutreach}
                disabled={loading}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 hover:from-indigo-500 hover:to-cyan-400 transition-all disabled:opacity-50"
              >
                {loading ? 'Generating AI Output...' : `Generate ${activeTab === 'cover_letter' ? 'Cover Letter' : 'Outreach Message'}`}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Generated Response:</span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied to Clipboard!' : 'Copy Text'}
                </button>
              </div>
              <textarea
                readOnly
                value={generatedText}
                rows={10}
                className="w-full p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-sm focus:outline-none resize-none font-mono"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
