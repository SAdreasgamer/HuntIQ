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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="pro-card max-w-md w-full overflow-hidden shadow-xl border border-slate-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded bg-slate-800 text-blue-400 border border-slate-700">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Upload Candidate Resume</h3>
              <p className="text-[11px] text-slate-400">PDF resume parsing & vector embedding</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          {!result ? (
            <>
              {/* Dropzone Area */}
              <label className="flex flex-col items-center justify-center p-6 border border-dashed border-slate-700 hover:border-blue-500 rounded-lg cursor-pointer bg-slate-900/60 hover:bg-slate-900 transition-colors">
                <UploadCloud className="h-8 w-8 text-slate-400 mb-2" />
                <span className="text-xs font-semibold text-slate-200">
                  {file ? file.name : 'Click to upload or drag & drop PDF'}
                </span>
                <span className="text-[11px] text-slate-500 mt-1">PDF format (Max 10MB)</span>
                <input type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
              </label>

              {error && (
                <div className="flex items-center gap-2 p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Parsing & Embedding...
                  </>
                ) : (
                  'Upload & Set Primary Resume'
                )}
              </button>
            </>
          ) : (
            <div className="text-center py-5 space-y-3">
              <CheckCircle2 className="h-10 w-10 text-emerald-400 mx-auto" />
              <div>
                <h4 className="text-base font-bold text-slate-100">Resume Uploaded Successfully</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Parsed <span className="text-blue-400 font-semibold">{result.skills_found?.length || 0} skills</span> & updated 384-dim embedding.
                </p>
              </div>
              <button
                onClick={onClose}
                className="px-5 py-1.5 rounded bg-blue-600 text-white font-semibold text-xs hover:bg-blue-500 transition-colors"
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
