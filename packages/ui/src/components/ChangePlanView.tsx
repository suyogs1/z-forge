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
    <div className="bg-[#0b1222] border border-slate-800 rounded-xl p-7 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-blue-500 via-indigo-500 to-transparent w-full" />
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-[11px] uppercase tracking-wider text-blue-400 font-mono font-bold">
              TOPOLOGICAL PROPOSAL ENGINE (T5)
            </span>
          </div>
          <h2 className="text-xl font-mono font-bold text-white tracking-tight flex items-center gap-3">
            Change Plan & Semantic Proposals
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-blue-950/60 text-blue-300 border border-blue-800/50">
              {proposals.length} Ordered Actions
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Proposals ordered topologically: copybooks first, dependent programs next, data layouts synchronized.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isApplied ? (
            <div className="flex items-center gap-2 px-3.5 py-2 bg-emerald-950/60 border border-emerald-600/40 rounded-lg text-emerald-300 text-xs font-mono font-semibold">
              <span className="text-emerald-400">✓</span>
              <span>Applied to {snapshotId}</span>
            </div>
          ) : (
            <button
              onClick={onApplySnapshot}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-blue-900/30 transition-all border border-blue-400/30 active:scale-95"
            >
              <span>APPLY TO SNAPSHOT</span>
              <span>&rarr;</span>
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3.5">
        {proposals.map((proposal, idx) => {
          return (
            <div
              key={proposal.id || idx}
              className="bg-[#070b14] border border-slate-800/80 rounded-xl p-4 transition-all hover:border-slate-700"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-800/60">
                <div className="flex items-center gap-3">
                  <span className="flex items-center justify-center w-6 h-6 rounded bg-slate-900 text-slate-300 font-mono text-xs font-bold border border-slate-800">
                    {idx + 1}
                  </span>
                  <div>
                    <span className="font-mono text-sm font-semibold text-slate-100 select-all">
                      {proposal.artifact_id}
                    </span>
                    <span className="ml-2 text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                      ID: {proposal.id}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {proposal.confidence !== undefined && (
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider block font-mono">Confidence</span>
                      <span className="font-mono text-xs font-semibold text-emerald-400">
                        {Math.round(proposal.confidence * 100)}%
                      </span>
                    </div>
                  )}
                  <span className={`text-[10px] font-mono px-2.5 py-1 rounded uppercase tracking-wider border ${
                    proposal.status === 'APPLIED' 
                      ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/50'
                      : 'bg-blue-950/40 text-blue-300 border-blue-800/50'
                  }`}>
                    {proposal.status || 'PROPOSED'}
                  </span>
                </div>
              </div>

              <div className="mb-2 text-xs text-slate-300 font-sans">
                <strong className="text-slate-400 font-mono uppercase text-[10px] mr-1.5">Action:</strong>
                {proposal.description}
              </div>

              {proposal.semantic_changes && proposal.semantic_changes.length > 0 && (
                <div className="space-y-2 mt-3 pt-2 border-t border-slate-800/40">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                    Semantic Field Mutation
                  </div>
                  {proposal.semantic_changes.map((change, scIdx) => (
                    <div 
                      key={scIdx} 
                      className="bg-[#0b101d] rounded-lg border border-slate-800 font-mono text-xs p-3"
                    >
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 pb-1 border-b border-slate-800">
                        <span className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/50 text-[10px]">
                            {change.kind}
                          </span>
                          <span className="text-slate-400">Line {change.line}</span>
                        </span>
                        <span className="text-slate-500 text-[10px]">{change.impact}</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                        <div className="bg-[#180a0f] border border-red-900/30 rounded p-2.5 text-red-300">
                          <div className="text-[9px] uppercase tracking-wider text-red-400/80 mb-1">Old Syntax</div>
                          <code className="text-red-200 select-all whitespace-pre font-mono block">{change.before}</code>
                        </div>
                        <div className="bg-[#071712] border border-emerald-900/30 rounded p-2.5 text-emerald-300">
                          <div className="text-[9px] uppercase tracking-wider text-emerald-400/80 mb-1">New Syntax</div>
                          <code className="text-emerald-200 select-all whitespace-pre font-mono block font-semibold">{change.after}</code>
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
