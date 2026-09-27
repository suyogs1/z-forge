import React from 'react'
import { AdversarialFinding, Proposal } from '../types'

interface AdversarialCriticCardProps {
  findings: AdversarialFinding[]
  remediationProposal?: Proposal
  onRemediate?: () => void
  isRemediated?: boolean
}

export const AdversarialCriticCard: React.FC<AdversarialCriticCardProps> = ({
  findings,
  remediationProposal,
  onRemediate,
  isRemediated = false,
}) => {
  const primaryFinding = findings[0] || {
    severity: 'CRITICAL',
    artifact: 'cobol/ACCTPROG.CBL',
    finding_type: 'LOCAL_VARIABLE_MISMATCH',
    evidence: 'CUSTOMER-ID is 12 bytes but WS-ACCT-CUST-ID remains X(8). Local Working-Storage assignment causes data truncation.',
    remediation: 'Expand WS-ACCT-CUST-ID from PIC X(8) to PIC X(12)',
  }

  return (
    <div className="bg-[#0b1222] border border-amber-500/40 rounded-xl p-7 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-amber-500 via-orange-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-[11px] uppercase tracking-wider text-amber-400 font-mono font-bold">
              ADVERSARIAL CRITIC ENGINE (T6)
            </span>
          </div>
          <h2 className="text-xl font-mono font-bold text-white tracking-tight flex items-center gap-3">
            Working-Storage Shadow Variable Audit
            <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/40">
              {findings.length} CRITICAL Finding
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Autonomous static-semantic critic inspecting un-aliased local variables across all blast radius programs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isRemediated ? (
            <div className="flex items-center gap-2 px-3.5 py-2 bg-emerald-950/60 border border-emerald-600/40 rounded-lg text-emerald-300 text-xs font-mono font-semibold">
              <span className="text-emerald-400">✓</span>
              <span>Remediation Applied to Snapshot 3</span>
            </div>
          ) : (
            <button
              onClick={onRemediate}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-amber-950/40 transition-all border border-amber-300/30 active:scale-95"
            >
              <span>APPLY REMEDIATION</span>
              <span>&rarr;</span>
            </button>
          )}
        </div>
      </div>

      {/* Critical Finding Card */}
      <div className="bg-[#070b14] border border-amber-500/50 rounded-xl p-5 mb-4">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-800">
          <div className="flex items-center gap-2 font-mono">
            <span className="px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold tracking-wider">
              {primaryFinding.severity}
            </span>
            <span className="text-xs text-slate-300">
              {primaryFinding.finding_type}
            </span>
          </div>
          <span className="font-mono text-xs text-slate-300 bg-slate-900 px-2.5 py-1 rounded border border-slate-800 select-all">
            {primaryFinding.artifact}
          </span>
        </div>

        <div className="space-y-3 font-mono text-xs">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">
              Critic Finding Evidence
            </div>
            <p className="text-xs text-amber-200 bg-amber-950/20 p-3 rounded-lg border border-amber-900/40 leading-relaxed font-mono">
              {primaryFinding.evidence}
            </p>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">
              Targeted Remediation Action
            </div>
            <div className="flex items-center justify-between bg-slate-900/90 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center gap-3">
                <span className="text-red-400 bg-red-950/40 px-2 py-0.5 rounded border border-red-900/40">
                  WS-ACCT-CUST-ID PIC X(8)
                </span>
                <span className="text-slate-400 font-bold">→</span>
                <span className="text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/40 font-bold">
                  WS-ACCT-CUST-ID PIC X(12)
                </span>
              </div>
              <span className="text-[11px] text-slate-400 hidden sm:inline">
                Topological Layer: COBOL Working-Storage Section
              </span>
            </div>
          </div>
        </div>
      </div>

      {remediationProposal && (
        <div className="bg-[#070b14]/80 border border-slate-800 rounded-lg p-3 text-xs font-mono">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
            Autonomous Patch Specification
          </div>
          <div className="text-slate-300">
            <span className="text-blue-400 font-bold">{remediationProposal.artifact_id}:</span> {remediationProposal.description}
          </div>
        </div>
      )}
    </div>
  )
}
