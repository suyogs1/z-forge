import React, { useState } from 'react'
import { ImpactedArtifact } from '../types'

interface ImpactGraphViewProps {
  impacted: ImpactedArtifact[]
  onProceed: () => void
}

const TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  COPYBOOK: { bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-800' },
  COBOL: { bg: 'bg-sky-950/60', text: 'text-sky-400', border: 'border-sky-800' },
  HLASM: { bg: 'bg-purple-950/60', text: 'text-purple-400', border: 'border-purple-800' },
  DATASET: { bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-800' },
  JCL: { bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-800' },
  AFP: { bg: 'bg-indigo-950/60', text: 'text-indigo-400', border: 'border-indigo-800' },
}

export const ImpactGraphView: React.FC<ImpactGraphViewProps> = ({ impacted, onProceed }) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL')

  const filtered = selectedFilter === 'ALL'
    ? impacted
    : impacted.filter((a) => a.type === selectedFilter)

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-400 bg-sky-950/60 border border-sky-800/80 px-2 py-0.5 rounded">
              Phase 2 &bull; Blast Radius Discovery
            </span>
            <span className="text-xs text-slate-400">Dependency &amp; Lineage Multi-Hop Graph</span>
          </div>
          <h3 className="text-lg font-bold text-white mt-1">
            Impacted Mainframe Topology ({impacted.length} Artifacts Discovered)
          </h3>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto text-xs">
          {['ALL', 'COPYBOOK', 'COBOL', 'HLASM', 'DATASET', 'JCL'].map((type) => (
            <button
              key={type}
              onClick={() => setSelectedFilter(type)}
              className={`px-2.5 py-1 rounded font-medium transition ${
                selectedFilter === type
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Visual Lineage Flow Pipeline */}
      <div className="py-6 overflow-x-auto">
        <div className="min-w-[700px] flex items-center justify-between px-4 py-3 bg-[#0a0f1d] border border-slate-800/80 rounded-lg">
          <div className="flex flex-col items-center text-center">
            <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Source Field</span>
            <span className="font-mono text-xs font-bold bg-sky-950 text-sky-300 border border-sky-800 px-2 py-1 rounded">
              CUSTOMER-ID
            </span>
          </div>

          <span className="text-slate-600 font-mono text-lg">&rarr;</span>

          <div className="flex flex-col items-center text-center">
            <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold mb-1">Copybook Tier</span>
            <span className="font-mono text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-1 rounded">
              CUSTMAST.CPY
            </span>
          </div>

          <span className="text-slate-600 font-mono text-lg">&rarr;</span>

          <div className="flex flex-col items-center text-center">
            <span className="text-[10px] uppercase tracking-wider text-sky-400 font-semibold mb-1">Program Tier</span>
            <span className="font-mono text-xs font-bold bg-sky-950 text-sky-300 border border-sky-800 px-2 py-1 rounded">
              COBOL &amp; HLASM
            </span>
          </div>

          <span className="text-slate-600 font-mono text-lg">&rarr;</span>

          <div className="flex flex-col items-center text-center">
            <span className="text-[10px] uppercase tracking-wider text-amber-400 font-semibold mb-1">Storage Tier</span>
            <span className="font-mono text-xs font-bold bg-amber-950 text-amber-300 border border-amber-800 px-2 py-1 rounded">
              DATASETS (DSD)
            </span>
          </div>

          <span className="text-slate-600 font-mono text-lg">&rarr;</span>

          <div className="flex flex-col items-center text-center">
            <span className="text-[10px] uppercase tracking-wider text-rose-400 font-semibold mb-1">Execution Tier</span>
            <span className="font-mono text-xs font-bold bg-rose-950 text-rose-300 border border-rose-800 px-2 py-1 rounded">
              BATCH JCL
            </span>
          </div>

          <span className="text-slate-600 font-mono text-lg">&rarr;</span>

          <div className="flex flex-col items-center text-center">
            <span className="text-[10px] uppercase tracking-wider text-indigo-400 font-semibold mb-1">Output Tier</span>
            <span className="font-mono text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-1 rounded">
              CUSTRPT.AFP
            </span>
          </div>
        </div>
      </div>

      {/* Grid of 9 Impacted Artifacts */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((art) => {
          const color = TYPE_COLORS[art.type] || {
            bg: 'bg-slate-900',
            text: 'text-slate-300',
            border: 'border-slate-700',
          }

          return (
            <div
              key={art.id || art.path}
              className="bg-[#0a0f1d] border border-slate-800/80 rounded-lg p-3.5 hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded border ${color.bg} ${color.text} ${color.border}`}
                  >
                    {art.type}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 truncate max-w-[120px]">
                    {art.reason}
                  </span>
                </div>

                <div className="font-mono text-sm font-semibold text-slate-200 truncate">
                  {art.path}
                </div>
              </div>

              <div className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                {art.details}
              </div>
            </div>
          )
        })}
      </div>

      {/* Bottom CTA to Step 3 */}
      <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
        <button
          onClick={onProceed}
          className="px-5 py-2.5 rounded-lg font-bold text-xs bg-sky-600 hover:bg-sky-500 text-white shadow-md shadow-sky-600/20 transition flex items-center space-x-1.5"
        >
          <span>GENERATE CHANGE PLAN</span>
          <span>&rarr;</span>
        </button>
      </div>
    </div>
  )
}
