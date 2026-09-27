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
    <div
      className={`border rounded-xl p-7 shadow-2xl relative overflow-hidden transition-all ${
        isFail
          ? 'bg-[#100b14] border-red-500/50 shadow-red-950/30'
          : 'bg-[#0b1222] border-emerald-500/40'
      }`}
    >
      {/* Top accent bar */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 ${
          isFail
            ? 'bg-gradient-to-r from-red-600 via-rose-500 to-amber-500'
            : 'bg-emerald-500'
        }`}
      />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                isFail ? 'bg-red-400 animate-pulse' : 'bg-emerald-400'
              }`}
            />
            <span
              className={`text-[11px] uppercase tracking-wider font-mono font-bold ${
                isFail ? 'text-red-400' : 'text-emerald-400'
              }`}
            >
              RUNTIME ADAPTER VERIFICATION
            </span>
            <span className="text-xs font-mono text-slate-500">• {snapshotName}</span>
          </div>
          <h2 className="text-xl font-mono font-bold text-white tracking-tight flex items-center gap-3">
            Initial Snapshot Execution
            <span
              className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded border ${
                isFail
                  ? 'bg-red-500/10 text-red-300 border-red-500/40'
                  : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/40'
              }`}
            >
              {isFail ? 'VALIDATION FAILED' : 'VALIDATION PASSED'}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            DeterministicScenarioAdapter executed against simulated customer records without external mainframe dependencies.
          </p>
        </div>

        {isFail && onAdvanceToCritic && (
          <button
            onClick={onAdvanceToCritic}
            className="self-start md:self-auto inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-amber-500/90 hover:bg-amber-400 text-slate-950 font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-amber-950/40 transition-all active:scale-95 border border-amber-300/30"
          >
            <span>RUN ADVERSARIAL CRITIC</span>
            <span>&rarr;</span>
          </button>
        )}
      </div>

      {isFail && (
        <div className="space-y-4">
          {/* Prominent High-Visibility Failure Diagnostic */}
          <div className="bg-[#180a0f] border border-red-500/60 rounded-xl p-6 shadow-inner">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-red-900/40">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-red-950 border border-red-600/60 flex items-center justify-center font-mono font-bold text-red-400 text-sm">
                  !
                </div>
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-red-400 font-bold">
                    Primary Diagnostic Result
                  </div>
                  <div className="text-2xl font-mono font-bold text-red-300 tracking-wider">
                    {validation.finding || 'DATA_TRUNCATION'}
                  </div>
                </div>
              </div>

              <div className="bg-red-950/60 border border-red-800/80 px-4 py-2 rounded-lg text-center font-mono">
                <div className="text-[10px] uppercase text-red-400/80 tracking-wider font-semibold">
                  Discrepancy
                </div>
                <div className="text-base font-bold text-red-200">
                  {validation.source_length || 12} bytes → {validation.destination_length || 8} bytes
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              <div className="bg-[#0b0609] p-3.5 rounded-lg border border-red-900/30">
                <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
                  Faulting Artifact
                </span>
                <span className="text-sm font-bold text-red-300 select-all">
                  {validation.artifact || 'cobol/ACCTPROG.CBL'}
                </span>
                <span className="text-[10px] text-slate-500 block mt-1">
                  Account Processing Main Module
                </span>
              </div>

              <div className="bg-[#0b0609] p-3.5 rounded-lg border border-red-900/30">
                <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
                  Root Cause Mechanism
                </span>
                <span className="text-sm font-bold text-amber-300">
                  Shadow Local Variable Mismatch
                </span>
                <span className="text-[10px] text-slate-400 block mt-1">
                  `WS-ACCT-CUST-ID` remains `PIC X(8)` in Working-Storage
                </span>
              </div>
            </div>

            <div className="mt-4 pt-3.5 border-t border-red-900/30 text-xs text-red-200/90 leading-relaxed font-sans">
              <strong>Failure Analysis:</strong> Although the shared copybook <code className="px-1.5 py-0.5 rounded bg-slate-900 text-amber-300 font-mono">CUSTMAST.CPY</code> was correctly resized to 12 bytes in Snapshot 2, the downstream program <code className="px-1.5 py-0.5 rounded bg-slate-900 text-red-300 font-mono">ACCTPROG.CBL</code> contains a locally declared shadow variable not inherited from any copybook. Moving the 12-byte identifier truncates the rightmost 4 bytes, which would lead to account collision in production.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

