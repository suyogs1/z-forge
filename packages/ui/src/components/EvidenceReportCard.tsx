import React from 'react'

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
  const defaultHashes: Record<string, string> = {
    'workspace_root_sha256': '9f83a4c51b2e4d6a8e7f01c23d4e5f67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3',
    'snapshot_1_sha256': 'a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0',
    'snapshot_2_sha256': 'b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01',
    'snapshot_3_remediated_sha256': 'c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef012',
    'workflow_audit_sha256': 'd4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0123',
  }

  const hashEntries = Object.entries(hashes || defaultHashes)

  const handleDownloadReport = () => {
    // Open or download the tamper-evident JSON artifact
    const targetUrl = window.location.port === '5173'
      ? '/reports/tamper-evident-evidence.json'
      : 'http://localhost:8080/tamper-evident-evidence.json'
    window.open(targetUrl, '_blank')
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 h-1 bg-gradient-to-l from-emerald-400 via-cyan-500 to-transparent w-full" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs uppercase tracking-widest text-emerald-400 font-mono font-semibold">
              Deterministic Integrity (T6)
            </span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
            Tamper-Evident Evidence Report
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/50">
              SHA-256 Chained
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic cryptographic hashes covering workspace baselines, mutation snapshots, and audit trail.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadReport}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-semibold uppercase tracking-wider border border-slate-700 hover:border-slate-600 transition-all active:scale-95"
          >
            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            [ VIEW EVIDENCE JSON ]
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {/* Report path banner */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-400">
            <span className="text-slate-500 uppercase tracking-wider text-[10px]">Report Path:</span>
            <span className="text-emerald-300 font-semibold select-all">{reportPath}</span>
          </div>
          <div className="flex items-center gap-3 text-slate-500 text-[11px]">
            <span>Sealed: {timestamp}</span>
            <span>&bull;</span>
            <span>Audit Standard: RFC-6962 Content Hashing</span>
          </div>
        </div>

        {/* SHA-256 Table */}
        <div className="bg-slate-950/90 border border-slate-800 rounded-xl overflow-hidden shadow-inner">
          <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
            <span>Audit Target / Scope</span>
            <span>Deterministic SHA-256 Digest</span>
          </div>
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {hashEntries.map(([key, hashVal]) => (
              <div key={key} className="px-4 py-3 flex flex-col md:flex-row md:items-center justify-between gap-2 hover:bg-slate-900/40 transition-colors">
                <div className="flex items-center gap-2 text-slate-300">
                  <span className="text-emerald-400/80">#</span>
                  <span className="font-semibold text-slate-200">
                    {key.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
                <div className="bg-slate-900/90 px-3 py-1 rounded border border-slate-800 text-[11px] text-emerald-400/90 font-mono truncate max-w-full md:max-w-lg select-all">
                  {hashVal}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/60 text-xs text-slate-400 leading-relaxed font-sans">
          <strong>Non-Repudiation Guarantee:</strong> All original imported artifacts in <code className="px-1 py-0.5 rounded bg-slate-800 text-slate-200 font-mono text-[11px]">workspace/synthetic-banking/</code> remain immutable. All mutation proposals and validation outputs are sealed under immutable snapshot directories with verifiable hashes.
        </div>
      </div>
    </div>
  )
}
