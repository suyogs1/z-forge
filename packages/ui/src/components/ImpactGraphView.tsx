import React, { useState } from 'react'
import { ImpactedArtifact } from '../types'

interface ImpactGraphViewProps {
  impacted: ImpactedArtifact[]
  onProceed: () => void
}

const TYPE_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  COPYBOOK: { bg: 'bg-emerald-950/40', text: 'text-emerald-400', border: 'border-emerald-800/60' },
  COBOL: { bg: 'bg-blue-950/40', text: 'text-blue-400', border: 'border-blue-800/60' },
  HLASM: { bg: 'bg-purple-950/40', text: 'text-purple-400', border: 'border-purple-800/60' },
  DATASET: { bg: 'bg-amber-950/40', text: 'text-amber-400', border: 'border-amber-800/60' },
  JCL: { bg: 'bg-rose-950/40', text: 'text-rose-400', border: 'border-rose-800/60' },
  AFP: { bg: 'bg-indigo-950/40', text: 'text-indigo-400', border: 'border-indigo-800/60' },
}

export const ImpactGraphView: React.FC<ImpactGraphViewProps> = ({ impacted, onProceed }) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL')

  const filtered = selectedFilter === 'ALL'
    ? impacted
    : impacted.filter((a) => a.type === selectedFilter)

  return (
    <div className="bg-[#0b1222] border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Top Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-blue-400 bg-blue-950/60 border border-blue-800/60 px-2 py-0.5 rounded">
              TOPOLOGICAL DISCOVERY
            </span>
            <span className="text-xs font-mono text-slate-400">Dependency & Lineage Graph Engine</span>
          </div>
          <h2 className="text-xl font-mono font-bold text-white tracking-tight mt-1.5 flex items-center gap-3">
            <span>Blast Radius Topology</span>
            <span className="text-xs font-mono font-normal text-slate-400">
              ({impacted.length} Artifacts &bull; 20 Dependencies &bull; 6 Lineage Relations)
            </span>
          </h2>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto text-xs font-mono">
          {['ALL', 'COPYBOOK', 'COBOL', 'HLASM', 'DATASET', 'JCL', 'AFP'].map((type) => (
            <button
              key={type}
              onClick={() => setSelectedFilter(type)}
              className={`px-3 py-1 rounded transition-colors ${
                selectedFilter === type
                  ? 'bg-blue-600 text-white font-medium shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Mainframe Topological Lineage Pipeline */}
      <div className="py-5">
        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
          <span>End-to-End Data Lineage Chain</span>
          <span className="text-slate-500">Topological Ordering: Copybooks → Programs → Storage → Batch → Output</span>
        </div>
        <div className="overflow-x-auto pb-2">
          <div className="min-w-[850px] grid grid-cols-6 gap-2 bg-[#070b14] border border-slate-800/80 p-3.5 rounded-lg shadow-inner text-center font-mono">
            <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
              <span className="text-[9px] uppercase tracking-wider text-slate-500 block mb-1">Origin Schema</span>
              <span className="text-xs font-bold text-sky-300">CUSTOMER-ID</span>
              <span className="text-[10px] text-slate-500 block mt-1">PIC X(8)</span>
            </div>

            <div className="p-2.5 rounded bg-emerald-950/20 border border-emerald-800/40">
              <span className="text-[9px] uppercase tracking-wider text-emerald-400/80 block mb-1">Copybook Tier</span>
              <span className="text-xs font-bold text-emerald-300">CUSTMAST.CPY</span>
              <span className="text-[10px] text-emerald-500 block mt-1">Shared Copybook</span>
            </div>

            <div className="p-2.5 rounded bg-blue-950/20 border border-blue-800/40">
              <span className="text-[9px] uppercase tracking-wider text-blue-400/80 block mb-1">Execution Tier</span>
              <span className="text-xs font-bold text-blue-300">COBOL Programs</span>
              <span className="text-[10px] text-blue-500 block mt-1">ACCTPROG, CUSTPROG</span>
            </div>

            <div className="p-2.5 rounded bg-purple-950/20 border border-purple-800/40">
              <span className="text-[9px] uppercase tracking-wider text-purple-400/80 block mb-1">DSECT Mirror</span>
              <span className="text-xs font-bold text-purple-300">CUSTDSCT.ASM</span>
              <span className="text-[10px] text-purple-500 block mt-1">HLASM Layout</span>
            </div>

            <div className="p-2.5 rounded bg-amber-950/20 border border-amber-800/40">
              <span className="text-[9px] uppercase tracking-wider text-amber-400/80 block mb-1">Dataset Tier</span>
              <span className="text-xs font-bold text-amber-300">CUST.MASTER.FILE</span>
              <span className="text-[10px] text-amber-500 block mt-1">Storage Record Layout</span>
            </div>

            <div className="p-2.5 rounded bg-indigo-950/20 border border-indigo-800/40">
              <span className="text-[9px] uppercase tracking-wider text-indigo-400/80 block mb-1">Output Stream</span>
              <span className="text-xs font-bold text-indigo-300">CUSTRPT.AFP</span>
              <span className="text-[10px] text-indigo-500 block mt-1">Print Presentation</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid of Impacted Artifact Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-1">
        {filtered.map((art) => {
          const style = TYPE_STYLES[art.type] || {
            bg: 'bg-slate-900',
            text: 'text-slate-300',
            border: 'border-slate-800',
          }

          return (
            <div
              key={art.id || art.path}
              className="bg-[#080d19] border border-slate-800/90 rounded-lg p-4 hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${style.bg} ${style.text} ${style.border}`}
                  >
                    {art.type}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {art.reason}
                  </span>
                </div>

                <div className="font-mono text-sm font-semibold text-slate-200 truncate select-all">
                  {art.path}
                </div>
              </div>

              <div className="text-xs text-slate-400 mt-2.5 leading-relaxed font-sans line-clamp-2">
                {art.details}
              </div>
            </div>
          )
        })}
      </div>

      {/* Bottom CTA to Step 3 */}
      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between">
        <span className="text-xs font-mono text-slate-500">
          Topological Sort: 9 artifacts ready for proposal generation
        </span>
        <button
          onClick={onProceed}
          className="px-5 py-2.5 rounded-lg font-mono font-bold text-xs uppercase tracking-wider bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30 transition-all border border-blue-400/30 flex items-center space-x-2"
        >
          <span>PROCEED TO CHANGE PLAN</span>
          <span>&rarr;</span>
        </button>
      </div>
    </div>
  )
}

