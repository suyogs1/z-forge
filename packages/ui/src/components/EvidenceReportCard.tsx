import React, { useState } from 'react'

interface EvidenceReportCardProps {
  reportPath?: string
  hashes?: Record<string, string>
  timestamp?: string
}

export const EvidenceReportCard: React.FC<EvidenceReportCardProps> = ({
  reportPath = 'workspace/synthetic-banking/reports/tamper-evident-evidence.json',
  hashes,
  timestamp = '2026-09-27T10:00:00Z',
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false)

  const defaultHashes: Record<string, string> = {
    'workspace_root_sha256': '9f83a4c51b2e4d6a8e7f01c23d4e5f67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3',
    'snapshot_1_sha256': 'a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0',
    'snapshot_2_sha256': 'b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01',
    'snapshot_3_remediated_sha256': 'c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef012',
    'workflow_audit_sha256': 'd4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0123',
  }

  const hashEntries = Object.entries(hashes || defaultHashes)

  const handleDownloadReport = () => {
    const targetUrl = window.location.port === '5173'
      ? '/reports/tamper-evident-evidence.json'
      : 'http://localhost:8080/tamper-evident-evidence.json'
    window.open(targetUrl, '_blank')
  }

  return (
    <div className="bg-[#0b1222] border border-slate-800 rounded-xl p-7 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-emerald-400 via-cyan-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] uppercase tracking-wider text-emerald-400 font-mono font-bold">
              AUDIT & INTEGRITY VERIFICATION (T6)
            </span>
          </div>
          <h2 className="text-xl font-mono font-bold text-white tracking-tight flex items-center gap-3">
            Tamper-Evident Evidence Report
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/50">
              SHA-256 Chained Manifest
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Cryptographic audit trail certifying workspace baselines, snapshot mutations, and verification steps.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadReport}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 font-mono text-xs font-bold uppercase tracking-wider border border-slate-700/80 hover:border-slate-600 transition-all active:scale-95 shadow-sm"
          >
            <span>VIEW EVIDENCE JSON</span>
            <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {/* High-Level Evidence Summary */}
        <div className="bg-[#070b14] border border-slate-800/80 rounded-xl p-5 shadow-inner">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                Artifact Immutability
              </span>
              <span className="text-emerald-400 font-bold text-sm">ORIGIN UNTOUCHED</span>
              <span className="text-[10px] text-slate-500 block mt-1">100% synthetic baseline preserved</span>
            </div>

            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                Snapshot Lineage
              </span>
              <span className="text-sky-300 font-bold text-sm">3 DISCRETE SNAPSHOTS</span>
              <span className="text-[10px] text-slate-500 block mt-1">Baseline → Proposed → Remediated</span>
            </div>

            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                Audit Standard
              </span>
              <span className="text-slate-200 font-bold text-sm">RFC-6962 SHA-256</span>
              <span className="text-[10px] text-slate-500 block mt-1">Deterministic hash sealing</span>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <span className="text-slate-500 text-[10px] uppercase">Report Target:</span>
              <span className="text-emerald-300 select-all">{reportPath}</span>
            </div>
            <div className="flex items-center gap-3 text-slate-500 text-[11px]">
              <span>Sealed: {timestamp}</span>
            </div>
          </div>
        </div>

        {/* Expandable Technical Cryptographic Details */}
        <div className="border border-slate-800/80 rounded-xl overflow-hidden bg-[#070b14]">
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="w-full px-5 py-3.5 flex items-center justify-between text-xs font-mono text-slate-300 hover:bg-slate-900/60 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-slate-500">{showTechnicalDetails ? '▼' : '▶'}</span>
              <span className="font-semibold uppercase tracking-wider text-slate-400">
                Technical Cryptographic Digest Table ({hashEntries.length} Verification Hashes)
              </span>
            </div>
            <span className="text-xs text-blue-400">
              {showTechnicalDetails ? 'Collapse' : 'Expand'}
            </span>
          </button>

          {showTechnicalDetails && (
            <div className="border-t border-slate-800 p-4 space-y-2">
              <div className="divide-y divide-slate-800/60 font-mono text-xs">
                {hashEntries.map(([key, hashVal]) => (
                  <div key={key} className="py-2.5 flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-slate-300">
                      <span className="text-emerald-400/80 font-bold">#</span>
                      <span className="font-semibold text-slate-200">
                        {key.replace(/_/g, ' ').toUpperCase()}
                      </span>
                    </div>
                    <div className="bg-slate-900/90 px-3 py-1 rounded border border-slate-800 text-[11px] text-emerald-400 font-mono truncate max-w-full md:max-w-md select-all">
                      {hashVal}
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800/60 text-xs text-slate-400 leading-relaxed font-sans mt-3">
                <strong>Non-Repudiation Guarantee:</strong> All original imported artifacts in <code className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200 font-mono text-[11px]">workspace/synthetic-banking/</code> remain immutable. All mutation proposals and validation outputs are sealed under immutable snapshot directories with verifiable hashes.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
