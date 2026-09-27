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
    // Open the existing AFP editor in a new browser tab/window
    // Either served via Vite plugin /reports/afp-custrpt.html or http://localhost:8080/afp-custrpt.html
    const targetUrl = window.location.port === '5173'
      ? '/reports/afp-custrpt.html'
      : 'http://localhost:8080/afp-custrpt.html'
    window.open(targetUrl, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-purple-500 via-pink-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            <span className="text-xs uppercase tracking-widest text-purple-400 font-mono font-semibold">
              Downstream Print Output Impact
            </span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
            AFP Output Impact
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/50">
              MO:DCA / PTX Stream
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            AFP is a downstream presentation artifact. Inspect physical print definitions and layout geometry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleOpenAfpEditor}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-purple-950/50 transition-all border border-purple-400/30 active:scale-95"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            [ INSPECT PRINT DEFINITION ]
          </button>
          {onNext && (
            <button
              onClick={onNext}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs font-semibold uppercase tracking-wider border border-slate-700 transition"
            >
              <span>[ VIEW EVIDENCE ]</span>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Preview Thumbnail Card */}
        <div className="lg:col-span-5 bg-slate-950/90 border border-slate-800 rounded-xl p-4 shadow-inner flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <div className="flex items-center gap-2 font-mono text-xs text-slate-200">
              <span className="text-purple-400">📄</span>
              <span className="font-semibold">{impact.document_name}</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              {impact.pages_count} Page • {impact.total_elements} Triads
            </span>
          </div>

          {/* Mini Print Thumbnail representation */}
          <div className="bg-white rounded p-4 text-slate-900 font-mono text-[10px] leading-tight shadow-md border border-slate-300 relative overflow-hidden select-none my-2">
            <div className="text-center font-bold border-b border-slate-300 pb-1 mb-2 tracking-wider text-[11px]">
              FIRST NATIONAL BANK - CUSTOMER STATEMENT
            </div>
            <div className="flex justify-between text-[9px] text-slate-600 mb-2">
              <span>DATE: 2026-09-27</span>
              <span>PAGE: 0001</span>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded p-1.5 mb-2">
              <span className="text-slate-500 block text-[8px] uppercase">Lineage Target:</span>
              <span className="font-bold text-purple-900">
                CUSTOMER ID: CUST-00000001
              </span>
              <span className="text-[8px] text-purple-700 ml-1 font-semibold">(Expanded to 12 Bytes)</span>
            </div>
            <div className="text-[8px] text-slate-500 space-y-1">
              <div className="flex justify-between border-t border-slate-200 pt-1">
                <span>ACCOUNT: 001-987654-20</span>
                <span>BALANCE: $14,250.00</span>
              </div>
            </div>
            <div className="absolute bottom-1 right-2 text-[8px] text-slate-400 font-sans italic">
              MO:DCA Synthetic Presentation Text
            </div>
          </div>

          <div className="flex items-center justify-between text-xs font-mono text-slate-400 pt-2 border-t border-slate-800/80">
            <span className="text-emerald-400 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              Structural analysis complete
            </span>
            <span className="text-slate-500">PAGEDEF/FORMDEF</span>
          </div>
        </div>

        {/* Impact Analysis Details */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2">
              Downstream Print Lineage
            </div>
            <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
              {impact.lineage_path.map((node, i) => (
                <React.Fragment key={i}>
                  <span className={`px-2 py-1 rounded text-xs border ${
                    i === impact.lineage_path.length - 1
                      ? 'bg-purple-950/80 text-purple-300 border-purple-700/60 font-bold'
                      : 'bg-slate-900 text-slate-300 border-slate-800'
                  }`}>
                    {node}
                  </span>
                  {i < impact.lineage_path.length - 1 && (
                    <span className="text-slate-500 font-bold">→</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2">
              Print Specification & Capacity
            </div>
            <div className="grid grid-cols-2 gap-3 mb-2 font-mono text-xs">
              <div className="bg-slate-900/80 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Field Print Width</span>
                <span className="text-purple-300 font-bold">
                  {impact.comparison?.before_capacity || 8} Bytes → {impact.comparison?.after_capacity || 12} Bytes
                </span>
              </div>
              <div className="bg-slate-900/80 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Layout Distortion</span>
                <span className="text-emerald-400 font-bold">
                  0 Shifts (Protected)
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              {impact.comparison?.explanation || 'Field expansion accommodated without page overflow or overlapping presentation text.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
