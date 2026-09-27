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

const STEP_LABELS = [
  '1. Request',
  '2. Blast Radius',
  '3. Change Plan',
  '4. Validation FAIL',
  '5. Critic Review',
  '6. Remediation',
  '7. Final PASS',
  '8. AFP Output',
  '9. Evidence',
]

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
  return (
    <header className="border-b border-slate-800 bg-[#0b1120]/90 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Logo & Product Positioning */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-sky-500 to-blue-700 flex items-center justify-center font-bold text-white shadow-lg shadow-sky-500/20 text-lg">
              ZF
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold tracking-wider text-xl text-white">Z-FORGE</span>
                <span className="text-[11px] font-semibold bg-sky-950 text-sky-400 border border-sky-800 px-2 py-0.5 rounded tracking-wide">
                  ENTERPRISE MAINFRAME
                </span>
                {isRunningWorkflow && (
                  <span className="flex items-center gap-1.5 text-[10px] font-mono bg-blue-950 text-blue-300 border border-blue-700/60 px-2 py-0.5 rounded animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                    RUNNING ENGINE
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-medium tracking-tight">
                AI Change Engineering for IBM Z &bull;{' '}
                <span className="text-slate-300">Understand the blast radius. Change safely. Prove the result.</span>
              </p>
            </div>
          </div>

          {/* Demo Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={onReset}
              className="text-xs px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium transition"
              title="Reset demo to initial change request"
            >
              Reset
            </button>
            <button
              onClick={onPrev}
              disabled={currentStep <= 1}
              className="text-xs px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 border border-slate-700 font-medium transition"
            >
              &larr; Prev
            </button>
            <button
              onClick={onNext}
              disabled={currentStep >= totalSteps}
              className="text-xs px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 border border-slate-700 font-medium transition"
            >
              Next &rarr;
            </button>
            <button
              onClick={onToggleAutoPlay}
              className={`text-xs px-3 py-1.5 rounded font-semibold transition flex items-center space-x-1.5 ${
                isAutoPlaying
                  ? 'bg-amber-600 text-white animate-pulse'
                  : 'bg-sky-600 hover:bg-sky-500 text-white shadow-sm shadow-sky-600/30'
              }`}
            >
              <span>{isAutoPlaying ? 'Pause Auto' : 'Auto-Play Demo'}</span>
            </button>
          </div>
        </div>

        {/* Narrative Progression Stepper Tabs */}
        <div className="mt-3 pt-2 border-t border-slate-800/80 overflow-x-auto no-scrollbar">
          <div className="flex items-center space-x-1.5 min-w-max pb-1">
            {STEP_LABELS.map((label, idx) => {
              const stepNumber = idx + 1
              const isActive = currentStep === stepNumber
              const isPast = currentStep > stepNumber

              // Highlight failure and critic states in distinctive colors
              let badgeColor = 'bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              if (isActive) {
                if (stepNumber === 4) badgeColor = 'bg-red-500/20 text-red-400 border border-red-500/50 shadow-sm shadow-red-500/20 font-bold'
                else if (stepNumber === 5) badgeColor = 'bg-amber-500/20 text-amber-400 border border-amber-500/50 shadow-sm shadow-amber-500/20 font-bold'
                else if (stepNumber === 7) badgeColor = 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-sm shadow-emerald-500/20 font-bold'
                else badgeColor = 'bg-sky-500/20 text-sky-400 border border-sky-500/50 shadow-sm shadow-sky-500/20 font-bold'
              } else if (isPast) {
                if (stepNumber === 4) badgeColor = 'text-red-400/80 bg-red-950/30'
                else if (stepNumber === 5) badgeColor = 'text-amber-400/80 bg-amber-950/30'
                else if (stepNumber === 7) badgeColor = 'text-emerald-400/80 bg-emerald-950/30'
                else badgeColor = 'text-slate-400 bg-slate-900/60'
              }

              return (
                <button
                  key={label}
                  onClick={() => onStepSelect(stepNumber)}
                  className={`text-[11px] px-2.5 py-1 rounded-md transition flex items-center space-x-1 ${badgeColor}`}
                >
                  <span>{label}</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </header>
  )
}
