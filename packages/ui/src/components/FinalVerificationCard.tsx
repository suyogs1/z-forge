import React from 'react'

interface FinalVerificationCardProps {
  status?: 'PASS' | 'FAIL'
  snapshotName?: string
  deterministicValidation?: string
  adversarialFindingsCount?: number
  evidenceGenerated?: boolean
  afpInspected?: boolean
  onNext?: () => void
}

export const FinalVerificationCard: React.FC<FinalVerificationCardProps> = ({
  status = 'PASS',
  snapshotName = 'Snapshot 3',
  deterministicValidation = 'PASS',
  adversarialFindingsCount = 0,
  evidenceGenerated = true,
  afpInspected = true,
  onNext,
}) => {
  return (
    <div className="bg-slate-900 border border-emerald-500/50 rounded-xl p-6 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-emerald-500 via-teal-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs uppercase tracking-widest text-emerald-400 font-mono font-bold">
              Autonomous Verification & Certification (T6)
            </span>
            <span className="text-xs font-mono text-slate-500">• {snapshotName}</span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-3">
            Final Verification
            <span className="text-xs font-mono font-bold px-3 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-sm shadow-emerald-950">
              {status}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Full deterministic scenario rerun against remediated Snapshot 3. Zero data truncation.
          </p>
        </div>

        {onNext && (
          <button
            onClick={onNext}
            className="self-start sm:self-auto inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-semibold uppercase tracking-wider shadow-lg shadow-emerald-950/40 transition-all active:scale-95"
          >
            <span>[ INSPECT DOWNSTREAM IMPACT ]</span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        )}
      </div>

      {/* Grid of Certification Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        {/* Metric 1 */}
        <div className="bg-slate-950/80 border border-emerald-900/40 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            Deterministic Runtime
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xl font-mono font-bold text-emerald-400">
              {deterministicValidation}
            </span>
            <div className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-600/50 flex items-center justify-center text-emerald-400">
              ✓
            </div>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            ACCTPROG truncation resolved
          </span>
        </div>

        {/* Metric 2 */}
        <div className="bg-slate-950/80 border border-emerald-900/40 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            Adversarial Critic
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xl font-mono font-bold text-emerald-400">
              {adversarialFindingsCount} Findings
            </span>
            <div className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-600/50 flex items-center justify-center text-emerald-400">
              ✓
            </div>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            All variables aligned
          </span>
        </div>

        {/* Metric 3 */}
        <div className="bg-slate-950/80 border border-emerald-900/40 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            Evidence Manifest
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xl font-mono font-bold text-emerald-400">
              {evidenceGenerated ? 'GENERATED' : 'PENDING'}
            </span>
            <div className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-600/50 flex items-center justify-center text-emerald-400">
              ✓
            </div>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            SHA-256 integrity chained
          </span>
        </div>

        {/* Metric 4 */}
        <div className="bg-slate-950/80 border border-emerald-900/40 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            AFP Output Impact
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xl font-mono font-bold text-emerald-400">
              {afpInspected ? 'INSPECTED' : 'PENDING'}
            </span>
            <div className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-600/50 flex items-center justify-center text-emerald-400">
              ✓
            </div>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            CUSTRPT.AFP print layout
          </span>
        </div>
      </div>

      <div className="bg-emerald-950/30 border border-emerald-800/40 rounded-lg p-3 text-xs text-emerald-300/90 font-mono flex items-center gap-2">
        <svg className="w-4 h-4 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>
          Verification status: <strong>CERTIFIED SAFE FOR PROMOTION</strong>. No residual data truncation across copybooks, programs, or print definitions.
        </span>
      </div>
    </div>
  )
}
