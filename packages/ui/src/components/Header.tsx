import React from 'react'

interface HeaderProps {
  currentStep: number
  totalSteps: number
  onStepSelect: (step: number) => void
  onPrev: () => void
  onNext: () => void
  isAutoPlaying: boolean
  onToggleAutoPlay: () => void
  onReset: () => void
  isRunningWorkflow: boolean
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  totalSteps,
  onStepSelect,
  onPrev,
  onNext,
  isAutoPlaying,
  onToggleAutoPlay,
  onReset,
  isRunningWorkflow,
}) => {
  const steps = [
    { num: 1, label: 'REQUEST', tag: 'INPUT' },
    { num: 2, label: 'BLAST RADIUS', tag: 'TOPOLOGY' },
    { num: 3, label: 'CHANGE PLAN', tag: 'PROPOSALS' },
    { num: 4, label: 'VALIDATION', tag: 'FAIL', isFail: true },
    { num: 5, label: 'CRITIC REVIEW', tag: 'RISK', isWarning: true },
    { num: 6, label: 'REMEDIATION', tag: 'PATCH' },
    { num: 7, label: 'FINAL PASS', tag: 'PASS', isSuccess: true },
    { num: 8, label: 'AFP OUTPUT', tag: 'PRINT' },
    { num: 9, label: 'EVIDENCE', tag: 'AUDIT' },
  ]

  return (
    <header className="border-b border-slate-800/80 bg-[#090d16]/95 backdrop-blur-md sticky top-0 z-40">
      {/* Top Utility and Branding Bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Logo & Product Positioning */}
          <div className="flex items-center space-x-3.5">
            <div className="h-9 w-9 rounded-lg bg-blue-600/90 border border-blue-400/40 flex items-center justify-center font-mono font-bold text-white shadow-sm shadow-blue-500/20 text-sm tracking-wider">
              ZF
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <span className="font-bold tracking-tight text-lg text-white">Z-FORGE</span>
                <span className="text-slate-600">|</span>
                <span className="text-xs font-medium text-slate-300 tracking-wide">
                  AI Change Engineering for IBM Z
                </span>
                <div className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono tracking-wider font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  SYSTEM READY
                </div>
                {isRunningWorkflow && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-blue-500/10 text-blue-400 border border-blue-500/30 animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                    EXECUTING ENGINE
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 font-mono tracking-tight mt-0.5">
                Understand the blast radius &bull; Change safely &bull; Prove the result
              </p>
            </div>
          </div>

          {/* Stepper Navigation & Demo Controls */}
          <div className="flex items-center space-x-2 self-start md:self-auto">
            <button
              onClick={onReset}
              className="text-xs font-mono px-3 py-1.5 rounded-md bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-colors"
              title="Reset workflow to Step 1"
            >
              Reset
            </button>
            <div className="flex items-center rounded-md border border-slate-700/80 bg-slate-900 divide-x divide-slate-800">
              <button
                onClick={onPrev}
                disabled={currentStep <= 1}
                className="text-xs font-mono px-2.5 py-1.5 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition-colors"
              >
                &larr; Prev
              </button>
              <button
                onClick={onNext}
                disabled={currentStep >= totalSteps}
                className="text-xs font-mono px-2.5 py-1.5 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition-colors"
              >
                Next &rarr;
              </button>
            </div>
            <button
              onClick={onToggleAutoPlay}
              className={`text-xs font-mono px-3 py-1.5 rounded-md font-semibold transition-all flex items-center space-x-1.5 ${
                isAutoPlaying
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-blue-600/90 hover:bg-blue-600 text-white border border-blue-500/40 shadow-sm'
              }`}
            >
              <span>{isAutoPlaying ? 'Pause Auto' : 'Auto Play'}</span>
            </button>
          </div>
        </div>

        {/* Polished Enterprise Workflow Progress Indicator */}
        <nav aria-label="Workflow Progress" className="mt-3 pt-2.5 border-t border-slate-800/80 overflow-x-auto no-scrollbar">
          <ol className="flex items-center min-w-max space-x-1 pb-1">
            {steps.map((st, idx) => {
              const isActive = currentStep === st.num
              const isPast = currentStep > st.num

              let itemStyle = 'bg-slate-900/40 text-slate-400 border-slate-800/80 hover:text-slate-200 hover:border-slate-700'
              let dotStyle = 'bg-slate-600'

              if (isActive) {
                if (st.isFail) {
                  itemStyle = 'bg-red-500/10 text-red-300 border-red-500/50 shadow-sm shadow-red-950 ring-1 ring-red-500/30'
                  dotStyle = 'bg-red-400 animate-pulse'
                } else if (st.isWarning) {
                  itemStyle = 'bg-amber-500/10 text-amber-300 border-amber-500/50 shadow-sm shadow-amber-950 ring-1 ring-amber-500/30'
                  dotStyle = 'bg-amber-400 animate-pulse'
                } else if (st.isSuccess) {
                  itemStyle = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/50 shadow-sm shadow-emerald-950 ring-1 ring-emerald-500/30'
                  dotStyle = 'bg-emerald-400'
                } else {
                  itemStyle = 'bg-blue-500/10 text-blue-300 border-blue-500/50 shadow-sm ring-1 ring-blue-500/30'
                  dotStyle = 'bg-blue-400'
                }
              } else if (isPast) {
                if (st.isFail) {
                  itemStyle = 'bg-red-950/20 text-red-400/80 border-red-900/30'
                  dotStyle = 'bg-red-500/60'
                } else if (st.isWarning) {
                  itemStyle = 'bg-amber-950/20 text-amber-400/80 border-amber-900/30'
                  dotStyle = 'bg-amber-500/60'
                } else if (st.isSuccess) {
                  itemStyle = 'bg-emerald-950/20 text-emerald-400/80 border-emerald-900/30'
                  dotStyle = 'bg-emerald-400'
                } else {
                  itemStyle = 'bg-slate-900/80 text-slate-300 border-slate-700/60'
                  dotStyle = 'bg-blue-400'
                }
              }

              return (
                <li key={st.num} className="flex items-center">
                  <button
                    onClick={() => onStepSelect(st.num)}
                    className={`text-[11px] font-mono font-medium px-2.5 py-1 rounded border transition-all flex items-center space-x-1.5 ${itemStyle}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${dotStyle}`} />
                    <span>{st.num}. {st.label}</span>
                  </button>
                  {idx < steps.length - 1 && (
                    <span className="text-slate-600/70 font-mono text-[10px] mx-1 select-none">
                      →
                    </span>
                  )}
                </li>
              )
            })}
          </ol>
        </nav>
      </div>
    </header>
  )
}

