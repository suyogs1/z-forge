import React from 'react'
import { AfpImpact } from '../types'

interface AfpImpactCardProps {
  afpImpact?: AfpImpact
  onNext?: () => void
}

export const AfpImpactCard: React.FC<AfpImpactCardProps> = ({
  afpImpact,
  onNext,
}) => {
  const defaultImpact: AfpImpact = {
    artifact: 'afp/CUSTRPT.AFP',
    document_name: 'CUSTRPT.AFP',
    pages_count: 1,
    total_elements: 7,
    lineage_path: [
      'CUSTOMER-ID (Schema)',
      'CUSTMAST.CPY (Copybook)',
      'CUSTRPT.CBL (Report Program)',
      'CUSTRPT.AFP (Print Output)',
    ],
    comparison: {
      before_capacity: 8,
      after_capacity: 12,
      source_schema_changed: true,
      afp_structure_changed: false,
      afp_layout_changed: false,
      explanation: 'Customer ID expanded to 12 bytes. MO:DCA stream structure preserved; print-record capacity increased.',
    },
    visualization_path: 'reports/afp-custrpt.html',
  }

  const impact = afpImpact || defaultImpact

  const handleOpenAfpEditor = () => {
    const targetUrl = window.location.port === '5173'
      ? '/reports/afp-custrpt.html'
      : 'http://localhost:8080/afp-custrpt.html'
    window.open(targetUrl, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="bg-[#0b1222] border border-slate-800 rounded-xl p-7 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-indigo-500 via-blue-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-[11px] uppercase tracking-wider text-indigo-400 font-mono font-bold">
              DOWNSTREAM OUTPUT IMPACT
            </span>
          </div>
          <h2 className="text-xl font-mono font-bold text-white tracking-tight flex items-center gap-3">
            AFP Print Stream Analysis
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/50">
              MO:DCA Structured Fields
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Downstream presentation verification: Inspect physical print definitions, PAGEDEF margins, and text triads.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleOpenAfpEditor}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-indigo-950/50 transition-all border border-indigo-400/30 active:scale-95"
          >
            <span>INSPECT PRINT DEFINITIONS</span>
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
          {onNext && (
            <button
              onClick={onNext}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs font-semibold uppercase tracking-wider border border-slate-700/80 transition"
            >
              <span>VIEW EVIDENCE</span>
              <span>&rarr;</span>
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Document Metadata Preview */}
        <div className="lg:col-span-5 bg-[#070b14] border border-slate-800/80 rounded-xl p-4 shadow-inner flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <div className="flex items-center gap-2 font-mono text-xs text-slate-200">
              <span className="text-indigo-400">📄</span>
              <span className="font-semibold select-all">{impact.document_name}</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-700">
              {impact.pages_count} Page • {impact.total_elements} Triads
            </span>
          </div>

          {/* Statement Layout Preview Box */}
          <div className="bg-[#0b101c] rounded-lg p-4 text-slate-200 font-mono text-xs border border-slate-800 relative select-none my-2 space-y-3">
            <div className="text-center font-bold border-b border-slate-800 pb-2 tracking-wider text-xs text-slate-300">
              FIRST NATIONAL BANK &bull; CUSTOMER STATEMENT
            </div>
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>DATE: 2026-09-27</span>
              <span>RECORD: CUSTRPT-001</span>
            </div>
            <div className="bg-indigo-950/30 border border-indigo-800/40 rounded p-2.5">
              <span className="text-slate-400 block text-[9px] uppercase tracking-wider">Lineage Output Field:</span>
              <div className="flex items-center justify-between mt-1">
                <span className="font-bold text-sky-300">
                  CUSTOMER ID: CUST-00000001
                </span>
                <span className="text-[10px] text-indigo-400 font-semibold">(12 Bytes)</span>
              </div>
            </div>
            <div className="text-[10px] text-slate-400 flex justify-between border-t border-slate-800 pt-2">
              <span>ACCOUNT: 001-987654-20</span>
              <span>BALANCE: $14,250.00</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs font-mono text-slate-400 pt-2.5 border-t border-slate-800/80">
            <span className="text-emerald-400 flex items-center gap-1.5 text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Structural verification complete
            </span>
            <span className="text-slate-500 text-[10px]">PAGEDEF / FORMDEF</span>
          </div>
        </div>

        {/* Lineage & Output Analysis */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-[#070b14] border border-slate-800/80 rounded-xl p-4">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2.5">
              End-to-End Output Lineage Path
            </div>
            <div className="space-y-1.5 font-mono text-xs">
              {(impact.lineage_path || []).map((step, idx) => (
                <div key={idx} className="flex items-center gap-2 text-slate-300">
                  <span className="text-indigo-400 font-bold">{idx + 1}.</span>
                  <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-[11px]">
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#070b14] border border-slate-800/80 rounded-xl p-4 text-xs font-mono">
            <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">
              Downstream Print Layout Behavior
            </div>
            <p className="text-slate-300 leading-relaxed font-sans text-xs">
              {impact.comparison?.explanation || 'Customer ID expanded to 12 bytes. MO:DCA stream structure preserved; print-record capacity increased without physical line overlap.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
