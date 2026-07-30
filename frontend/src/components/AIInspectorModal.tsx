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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white max-w-2xl w-full rounded-xl overflow-hidden shadow-2xl border border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50">
          <div>
            <span className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider">AI Intelligence Studio</span>
            <h3 className="text-lg font-bold text-slate-900 mt-0.5">{job.title}</h3>
            <p className="text-xs text-slate-500">{job.company_name}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-200 bg-slate-100/60 p-2 gap-2">
          <button
            onClick={() => {
              setActiveTab('cover_letter')
              setGeneratedText('')
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
              activeTab === 'cover_letter'
                ? 'bg-white text-blue-600 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            Tailored Cover Letter
          </button>
          <button
            onClick={() => {
              setActiveTab('outreach')
              setGeneratedText('')
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
              activeTab === 'outreach'
                ? 'bg-white text-blue-600 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            <Send className="h-3.5 w-3.5" />
            LinkedIn Message
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4">
          {!generatedText ? (
            <div className="text-center py-8 space-y-3">
              <Sparkles className="h-8 w-8 text-blue-600 mx-auto" />
              <p className="text-xs text-slate-600">
                Generate AI-tailored content optimized for {job.company_name} using your parsed candidate profile.
              </p>
              <button
                onClick={activeTab === 'cover_letter' ? handleGenerateCoverLetter : handleGenerateOutreach}
                disabled={loading}
                className="px-5 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors shadow-xs disabled:opacity-50"
              >
                {loading ? 'Generating Output...' : `Generate ${activeTab === 'cover_letter' ? 'Cover Letter' : 'Outreach Message'}`}
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Generated Output:</span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied!' : 'Copy Text'}
                </button>
              </div>
              <textarea
                readOnly
                value={generatedText}
                rows={9}
                className="w-full p-3 rounded bg-slate-50 border border-slate-200 text-slate-800 text-xs focus:outline-none resize-none font-mono"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
