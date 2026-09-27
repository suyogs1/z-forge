import React from 'react'
import { Proposal } from '../types'

interface ChangePlanViewProps {
  proposals: Proposal[]
  onApplySnapshot?: () => void
  isApplied?: boolean
  snapshotId?: string
}

export const ChangePlanView: React.FC<ChangePlanViewProps> = ({
  proposals,
  onApplySnapshot,
  isApplied = false,
  snapshotId = 'snapshot-2',
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-blue-500 via-indigo-500 to-transparent w-full" />
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-xs uppercase tracking-widest text-blue-400 font-mono font-semibold">
              Topological Change Engine (T5)
            </span>
          </div>
          <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
            Change Proposals
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 border border-blue-700/50">
              {proposals.length} Ordered Actions
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Proposals ordered topologically: copybooks first, dependent programs next, data layouts synchronized.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isApplied ? (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-950/60 border border-emerald-600/50 rounded-lg text-emerald-400 text-xs font-mono">
              <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Applied to {snapshotId}</span>
            </div>
          ) : (
            <button
              onClick={onApplySnapshot}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold uppercase tracking-wider shadow-lg shadow-blue-900/30 transition-all border border-blue-400/30 active:scale-95"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
              [ APPLY TO SNAPSHOT ]
            </button>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {proposals.map((proposal, idx) => {
          return (
            <div
              key={proposal.id || idx}
              className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-4 transition-all hover:border-slate-700 hover:bg-slate-950/90"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-800/60">
                <div className="flex items-center gap-3">
                  <span className="flex items-center justify-center w-6 h-6 rounded bg-slate-800 text-slate-300 font-mono text-xs font-bold">
                    {idx + 1}
                  </span>
                  <div>
                    <span className="font-mono text-sm font-semibold text-slate-100">
                      {proposal.artifact_id}
                    </span>
                    <span className="ml-2 text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                      ID: {proposal.id}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {proposal.confidence !== undefined && (
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Confidence</span>
                      <span className="font-mono text-xs font-semibold text-emerald-400">
                        {Math.round(proposal.confidence * 100)}%
                      </span>
                    </div>
                  )}
                  <span className={`text-[10px] font-mono px-2 py-1 rounded uppercase tracking-wider border ${
                    proposal.status === 'APPLIED' 
                      ? 'bg-emerald-950/50 text-emerald-400 border-emerald-800/50'
                      : 'bg-blue-950/50 text-blue-400 border-blue-800/50'
                  }`}>
                    {proposal.status || 'PROPOSED'}
                  </span>
                </div>
              </div>

              <div className="mb-3">
                <span className="text-xs text-slate-400">
                  <strong className="text-slate-300">Reason:</strong> {proposal.description}
                </span>
              </div>

              {proposal.semantic_changes && proposal.semantic_changes.length > 0 && (
                <div className="space-y-2 mt-2">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                    Semantic Field Mutations
                  </div>
                  {proposal.semantic_changes.map((change, scIdx) => (
                    <div 
                      key={scIdx} 
                      className="bg-slate-900/90 rounded border border-slate-800/90 font-mono text-xs overflow-x-auto p-3"
                    >
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 pb-1 border-b border-slate-800">
                        <span className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/50 text-[10px]">
                            {change.kind}
                          </span>
                          <span className="text-slate-400">Line {change.line}</span>
                        </span>
                        <span className="text-slate-500 text-[10px]">{change.impact}</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                        <div className="bg-red-950/20 border border-red-900/30 rounded p-2 text-red-300">
                          <div className="text-[9px] uppercase tracking-wider text-red-400/80 mb-1">Old Value</div>
                          <code className="text-red-200 select-all whitespace-pre font-mono">{change.before}</code>
                        </div>
                        <div className="bg-emerald-950/20 border border-emerald-900/30 rounded p-2 text-emerald-300">
                          <div className="text-[9px] uppercase tracking-wider text-emerald-400/80 mb-1">New Value</div>
                          <code className="text-emerald-200 select-all whitespace-pre font-mono">{change.after}</code>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
