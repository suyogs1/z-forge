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
    <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Accent corner line */}
      <div className="absolute top-0 left-0 w-1.5 h-full bg-sky-500" />

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-400 bg-sky-950/60 border border-sky-800/80 px-2 py-0.5 rounded">
              Phase 1 &bull; Change Request
            </span>
            <span className="text-xs text-slate-400">Target Field Expansion</span>
          </div>

          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-3">
            <span className="font-mono bg-slate-900 border border-slate-700 px-2.5 py-1 rounded text-sky-300">
              {fieldName}
            </span>
            <span className="text-slate-400 text-sm font-normal">
              Mainframe Enterprise Customer Identifier
            </span>
          </h2>

          <p className="text-sm text-slate-300 mt-2 max-w-2xl leading-relaxed">
            Expand field capacity to accommodate standard 12-character regional bank identifiers across all core banking COBOL, copybook, HLASM assembler, JCL jobs, and print streams.
          </p>
        </div>

        {/* Capacity Comparison Badge & CTA */}
        <div className="flex flex-col sm:flex-row items-center gap-4 bg-[#0a0f1d] border border-slate-800/90 p-4 rounded-xl">
          <div className="flex items-center space-x-3 text-center sm:text-left">
            <div>
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Current</div>
              <div className="font-mono text-base font-bold text-slate-200">{currentPic}</div>
              <div className="text-[11px] text-slate-500 font-mono">{oldLen} bytes</div>
            </div>

            <div className="text-sky-400 font-bold text-xl px-1">&rarr;</div>

            <div>
              <div className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider">Target</div>
              <div className="font-mono text-base font-bold text-sky-300">{targetPic}</div>
              <div className="text-[11px] text-sky-400/80 font-mono">{newLen} bytes</div>
            </div>
          </div>

          <div className="h-8 w-[1px] bg-slate-800 hidden sm:block" />

          <button
            onClick={onAnalyze}
            disabled={isLoading}
            className="w-full sm:w-auto px-6 py-3 rounded-lg font-bold text-sm bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white shadow-lg shadow-sky-500/25 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
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
              <span>Re-Analyze Change</span>
            ) : (
              <span>ANALYZE CHANGE</span>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
