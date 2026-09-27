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
    <div className="bg-slate-900 border border-amber-500/40 rounded-xl p-6 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-amber-500 via-orange-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-xs uppercase tracking-widest text-amber-400 font-mono font-bold">
              Autonomous Adversarial Critic Pass (T6)
            </span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
            Adversarial Audit
            <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/50">
              {findings.length} Uncovered Risk{findings.length === 1 ? '' : 's'}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Adversarial static analysis inspecting Working-Storage local declarations for un-aliased shadow variables.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isRemediated ? (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-950/70 border border-emerald-600/50 rounded-lg text-emerald-400 text-xs font-mono">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Remediation Proposed & Applied</span>
            </div>
          ) : (
            <button
              onClick={onRemediate}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-amber-950/40 transition-all border border-amber-300/30 active:scale-95"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              [ REMEDIATE ]
            </button>
          )}
        </div>
      </div>

      {/* Critical Finding Card */}
      <div className="bg-slate-950/90 border border-amber-600/60 rounded-xl p-5 mb-4">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-400 border border-amber-500/50 text-xs font-mono font-bold tracking-wider uppercase">
              {primaryFinding.severity}
            </span>
            <span className="font-mono text-xs text-slate-400">
              {primaryFinding.finding_type}
            </span>
          </div>
          <span className="font-mono text-xs text-slate-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            {primaryFinding.artifact}
          </span>
        </div>

        <div className="space-y-3">
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-1">
              Critic Evidence
            </div>
            <p className="text-sm font-mono text-amber-200 bg-amber-950/30 p-3 rounded-lg border border-amber-900/40">
              {primaryFinding.evidence}
            </p>
          </div>

          <div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-1">
              Targeted Remediation
            </div>
            <div className="flex items-center gap-4 bg-slate-900 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center gap-3 font-mono text-sm">
                <span className="text-red-400 bg-red-950/40 px-2 py-1 rounded border border-red-900/40">
                  PIC X(8)
                </span>
                <span className="text-slate-400">→</span>
                <span className="text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded border border-emerald-900/40 font-bold">
                  PIC X(12)
                </span>
              </div>
              <span className="text-xs text-slate-400 font-mono hidden sm:inline">
                ({primaryFinding.remediation})
              </span>
            </div>
          </div>
        </div>
      </div>

      {remediationProposal && (
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3 text-xs font-mono">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
            Generated Proposal Patch
          </div>
          <div className="text-slate-300">
            <span className="text-blue-400">{remediationProposal.artifact_id}:</span> {remediationProposal.description}
          </div>
        </div>
      )}
    </div>
  )
}
