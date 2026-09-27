import React from 'react'
import { WorkflowResult } from '../types'

interface ChangeRequestCardProps {
  data: WorkflowResult
  onAnalyze: () => void
  isLoading: boolean
  isCompleted: boolean
}

export const ChangeRequestCard: React.FC<ChangeRequestCardProps> = ({
  data,
  onAnalyze,
  isLoading,
  isCompleted,
}) => {
  const req = data.change_request
  const fieldName = req.field_name || req.field || 'CUSTOMER-ID'
  const oldLen = req.old_length || 8
  const newLen = req.new_length || 12
  const currentPic = `PIC X(${oldLen})`
  const targetPic = req.target_type || req.target || `PIC X(${newLen})`

  return (
    <div className="bg-[#0b1222] border border-slate-800 rounded-xl p-7 shadow-2xl relative overflow-hidden">
      {/* Subtle top indicator bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 via-sky-500 to-indigo-600" />

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8">
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-blue-400 bg-blue-950/60 border border-blue-800/60 px-2.5 py-0.5 rounded">
              CHANGE SPECIFICATION
            </span>
            <span className="text-xs font-mono text-slate-400">Target: Core Banking Workspace</span>
          </div>

          <div>
            <div className="text-xs uppercase font-mono tracking-wider text-slate-400">
              Field Expansion
            </div>
            <h1 className="text-2xl sm:text-3xl font-mono font-bold text-white tracking-tight flex items-center gap-3 mt-1">
              <span className="text-sky-300 bg-slate-900/90 border border-slate-700/80 px-3 py-1 rounded">
                {fieldName}
              </span>
            </h1>
          </div>

          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Expand field byte width across all shared copybooks, COBOL programs, HLASM dsects, JCL catalog datasets, and downstream AFP output streams to eliminate customer record truncation.
          </p>
        </div>

        {/* Hero Field Transformation Box & Action Button */}
        <div className="flex flex-col sm:flex-row items-center gap-6 bg-[#070b14] border border-slate-800/90 p-5 rounded-xl shadow-inner">
          <div className="flex items-center space-x-4 text-center sm:text-left">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Current Definition</div>
              <div className="font-mono text-lg font-bold text-slate-200">{currentPic}</div>
              <div className="text-[11px] text-slate-500 font-mono">{oldLen} Bytes</div>
            </div>

            <div className="text-blue-400 font-mono font-bold text-2xl px-2">→</div>

            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-sky-400">Target Definition</div>
              <div className="font-mono text-lg font-bold text-sky-300">{targetPic}</div>
              <div className="text-[11px] text-sky-400/80 font-mono">{newLen} Bytes</div>
            </div>
          </div>

          <div className="h-10 w-[1px] bg-slate-800 hidden sm:block" />

          <button
            onClick={onAnalyze}
            disabled={isLoading}
            className="w-full sm:w-auto px-7 py-3.5 rounded-lg font-mono font-bold text-xs uppercase tracking-wider bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/30 transition-all border border-blue-400/30 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Analyzing Workspace...</span>
              </>
            ) : isCompleted ? (
              <span>RE-ANALYZE CHANGE</span>
            ) : (
              <span>ANALYZE CHANGE</span>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

