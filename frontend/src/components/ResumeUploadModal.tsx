import React, { useState } from 'react'
import { X, UploadCloud, CheckCircle2, AlertCircle, FileText, Loader2 } from 'lucide-react'

interface ResumeUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export const ResumeUploadModal: React.FC<ResumeUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState<boolean>(false)
  const [result, setResult] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0]
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Please select a valid PDF file.')
        setFile(null)
        return
      }
      setFile(selected)
      setError(null)
      setResult(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/v1/resumes/upload', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Resume upload failed')
      }

      const data = await res.json()
      setResult(data)
      onSuccess()
    } catch (err: any) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
      <div className="glass-card max-w-lg w-full rounded-2xl border border-slate-700 overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Upload Candidate Resume</h3>
              <p className="text-xs text-slate-400">PDF resume parsing & vector embedding</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {!result ? (
            <>
              {/* Dropzone Area */}
              <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-2xl cursor-pointer bg-slate-900/40 hover:bg-slate-900/80 transition-all group">
                <UploadCloud className="h-10 w-10 text-slate-400 group-hover:text-indigo-400 transition-colors mb-3" />
                <span className="text-sm font-semibold text-slate-200">
                  {file ? file.name : 'Click to upload or drag & drop PDF'}
                </span>
                <span className="text-xs text-slate-500 mt-1">PDF format (Max 10MB)</span>
                <input type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
              </label>

              {error && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 hover:from-indigo-500 hover:to-cyan-400 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Parsing & Embedding Resume...
                  </>
                ) : (
                  'Upload & Set Primary Resume'
                )}
              </button>
            </>
          ) : (
            <div className="text-center py-6 space-y-4">
              <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto" />
              <div>
                <h4 className="text-lg font-bold text-white">Resume Successfully Uploaded!</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Extracted <span className="text-indigo-400 font-semibold">{result.skills_found?.length || 0} skills</span> and built 384-dim dense vector embedding.
                </p>
              </div>
              <button
                onClick={onClose}
                className="px-6 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold text-sm shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition-all"
              >
                Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
