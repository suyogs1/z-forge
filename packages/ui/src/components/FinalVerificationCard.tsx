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
    <div className="bg-[#0b1222] border border-emerald-500/50 rounded-xl p-7 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-emerald-500 via-teal-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] uppercase tracking-wider text-emerald-400 font-mono font-bold">
              AUTONOMOUS VERIFICATION & CERTIFICATION
            </span>
            <span className="text-xs font-mono text-slate-500">• {snapshotName}</span>
          </div>
          <h2 className="text-xl font-mono font-bold text-white tracking-tight flex items-center gap-3">
            Change Verification Status
            <span className="text-xs font-mono font-bold px-3 py-1 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-950">
              CHANGE VERIFIED &bull; {status}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Deterministic scenario rerun against remediated Snapshot 3. Zero data truncation.
          </p>
        </div>

        {onNext && (
          <button
            onClick={onNext}
            className="self-start sm:self-auto inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-emerald-950/40 transition-all active:scale-95 border border-emerald-400/30"
          >
            <span>INSPECT DOWNSTREAM IMPACT</span>
            <span>&rarr;</span>
          </button>
        )}
      </div>

      {/* Prominent Verification Summary Banner */}
      <div className="bg-[#070b14] border border-emerald-500/40 rounded-xl p-5 mb-5 shadow-inner">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-950 border border-emerald-600/50 flex items-center justify-center font-mono font-bold text-emerald-400 text-lg">
              ✓
            </div>
            <div>
              <div className="text-sm font-mono font-bold text-emerald-300">
                CHANGE VERIFIED — PRODUCTION READY
              </div>
              <div className="text-xs text-slate-400 font-mono mt-0.5">
                All 9 blast-radius artifacts synchronized across copybooks, programs, datasets, and JCL.
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="bg-slate-900 px-3 py-1.5 rounded border border-slate-800 text-center">
              <span className="text-[10px] text-slate-500 block uppercase">Inconsistencies</span>
              <span className="text-emerald-400 font-bold text-sm">0 Remaining</span>
            </div>
            <div className="bg-slate-900 px-3 py-1.5 rounded border border-slate-800 text-center">
              <span className="text-[10px] text-slate-500 block uppercase">Adversarial Findings</span>
              <span className="text-emerald-400 font-bold text-sm">0 Findings</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid of Certification Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-4">
        {/* Metric 1 */}
        <div className="bg-[#070b14] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            Runtime Scenarios
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-mono font-bold text-emerald-400">
              {deterministicValidation}
            </span>
            <span className="text-xs font-mono text-emerald-500 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
              CLEAN
            </span>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            ACCTPROG truncation resolved
          </span>
        </div>

        {/* Metric 2 */}
        <div className="bg-[#070b14] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            Adversarial Critic
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-mono font-bold text-emerald-400">
              {adversarialFindingsCount} Findings
            </span>
            <span className="text-xs font-mono text-emerald-500 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
              RESOLVED
            </span>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            Working-Storage aligned
          </span>
        </div>

        {/* Metric 3 */}
        <div className="bg-[#070b14] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            Evidence Manifest
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-mono font-bold text-emerald-400">
              {evidenceGenerated ? 'GENERATED' : 'PENDING'}
            </span>
            <span className="text-xs font-mono text-emerald-500 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
              SEALED
            </span>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            SHA-256 integrity chained
          </span>
        </div>

        {/* Metric 4 */}
        <div className="bg-[#070b14] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            AFP Output Impact
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-mono font-bold text-emerald-400">
              {afpInspected ? 'INSPECTED' : 'PENDING'}
            </span>
            <span className="text-xs font-mono text-emerald-500 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
              VALID
            </span>
          </div>
          <span className="text-[10px] text-slate-500 mt-2 font-mono">
            CUSTRPT.AFP print layout
          </span>
        </div>
      </div>

      <div className="bg-emerald-950/20 border border-emerald-800/40 rounded-lg p-3 text-xs text-emerald-300 font-mono flex items-center gap-2">
        <span className="text-emerald-400 font-bold">✓</span>
        <span>
          Verification status: <strong>CERTIFIED FOR PRODUCTION PROMOTION</strong>. 0 remaining inconsistencies, 0 adversarial findings across all topological tiers.
        </span>
      </div>
    </div>
  )
}
