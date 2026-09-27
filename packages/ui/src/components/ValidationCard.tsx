import React from 'react'
import { ValidationResult } from '../types'

interface ValidationCardProps {
  validation: ValidationResult
  snapshotName?: string
  onAdvanceToCritic?: () => void
}

export const ValidationCard: React.FC<ValidationCardProps> = ({
  validation,
  snapshotName = 'Snapshot 2',
  onAdvanceToCritic,
}) => {
  const isFail = validation.status === 'FAIL'

  return (
    <div className={`border rounded-xl p-6 shadow-2xl relative overflow-hidden transition-all ${
      isFail
        ? 'bg-gradient-to-br from-red-950/40 via-slate-900 to-slate-950 border-red-500/60 shadow-red-950/40 ring-1 ring-red-500/20'
        : 'bg-slate-900 border-emerald-500/40'
    }`}>
      {/* Visual pulse accent */}
      {isFail && (
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-red-600 via-rose-500 to-amber-500 animate-pulse" />
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`w-2.5 h-2.5 rounded-full ${isFail ? 'bg-red-500 animate-ping' : 'bg-emerald-400'}`} />
            <span className={`text-xs uppercase tracking-widest font-mono font-bold ${
              isFail ? 'text-red-400' : 'text-emerald-400'
            }`}>
              Deterministic Runtime Verification (T6)
            </span>
            <span className="text-xs font-mono text-slate-500">• {snapshotName}</span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-3">
            Initial Snapshot Validation
            <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${
              isFail 
                ? 'bg-red-500/20 text-red-400 border-red-500/50 shadow-sm shadow-red-900/40'
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
            }`}>
              {validation.status}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic execution against synthetic datasets without cloud or z/OS dependencies.
          </p>
        </div>

        {isFail && onAdvanceToCritic && (
          <button
            onClick={onAdvanceToCritic}
            className="self-start md:self-auto inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-amber-950/40 transition-all active:scale-95"
          >
            <span>[ RUN ADVERSARIAL CRITIC ]</span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        )}
      </div>

      {isFail && (
        <div className="space-y-4">
          {/* Prominent Failure Banner */}
          <div className="bg-red-950/60 border-2 border-red-600/70 rounded-xl p-5 shadow-inner">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-red-900/50 rounded-lg border border-red-500/60 text-red-400 shrink-0">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="font-mono text-lg font-black text-red-400 tracking-wider">
                    {validation.finding || 'DATA_TRUNCATION'}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-red-900/80 text-red-200 text-xs font-mono font-semibold border border-red-700">
                    High Impact Planted Failure
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                  <div className="bg-slate-950/80 p-3 rounded-lg border border-red-900/40">
                    <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
                      Faulting Artifact
                    </span>
                    <span className="font-mono text-sm font-bold text-red-300">
                      {validation.artifact || 'cobol/ACCTPROG.CBL'}
                    </span>
                  </div>

                  <div className="bg-slate-950/80 p-3 rounded-lg border border-red-900/40">
                    <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
                      Byte Discrepancy
                    </span>
                    <div className="flex items-center gap-2 font-mono text-sm font-bold">
                      <span className="text-amber-400">{validation.source_length || 12} bytes (source)</span>
                      <span className="text-slate-500">→</span>
                      <span className="text-red-400">{validation.destination_length || 8} bytes (destination)</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-red-900/40 text-xs text-red-200/90 leading-relaxed font-sans">
                  <strong>Root Cause Analysis:</strong> While the shared copybook <code className="px-1.5 py-0.5 rounded bg-slate-900 text-amber-300 font-mono">CUSTMAST.CPY</code> was successfully resized to 12 bytes, the program contains an un-aliased local Working-Storage variable <code className="px-1.5 py-0.5 rounded bg-slate-900 text-red-300 font-mono">WS-ACCT-CUST-ID</code> still defined as <code className="font-mono text-amber-300">PIC X(8)</code>. Moving 12-byte customer data causes silent truncation on z/OS.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
