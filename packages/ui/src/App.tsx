import React, { useState, useEffect, useRef } from 'react'
import { Header } from './components/Header'
import { ChangeRequestCard } from './components/ChangeRequestCard'
import { ImpactGraphView } from './components/ImpactGraphView'
import { ChangePlanView } from './components/ChangePlanView'
import { ValidationCard } from './components/ValidationCard'
import { AdversarialCriticCard } from './components/AdversarialCriticCard'
import { FinalVerificationCard } from './components/FinalVerificationCard'
import { AfpImpactCard } from './components/AfpImpactCard'
import { EvidenceReportCard } from './components/EvidenceReportCard'
import { WorkflowResult, DEFAULT_WORKFLOW_DATA } from './types'

export const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<number>(1)
  const [workflowData, setWorkflowData] = useState<WorkflowResult>(DEFAULT_WORKFLOW_DATA)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [isAutoPlaying, setIsAutoPlaying] = useState<boolean>(false)
  const [viewMode, setViewMode] = useState<'progressive' | 'all'>('progressive')
  
  // Section refs for smooth scrolling
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([])

  // Attempt live workflow fetch from Vite proxy or direct API
  const fetchLiveWorkflow = async () => {
    setIsLoading(true)
    try {
      // First try static pre-generated result from execute_workflow
      let res = await fetch('/reports/workflow-result.json')
      if (!res.ok) {
        res = await fetch('/api/workflow')
      }
      if (res.ok) {
        const data = await res.json()
        if (data && data.impacted_artifacts) {
          setWorkflowData((prev) => ({
            ...prev,
            ...data,
            change_request: { ...prev.change_request, ...(data.change_request || {}) },
            first_validation: { ...prev.first_validation, ...(data.first_validation || {}) },
            second_validation: { ...prev.second_validation, ...(data.second_validation || {}) },
            final_validation: { ...prev.final_validation, ...(data.final_validation || {}) },
            afp_impact: { ...prev.afp_impact, ...(data.afp_impact || {}) },
          }))
        }
      }
    } catch {
      // Retain DEFAULT_WORKFLOW_DATA which matches execute_workflow(...)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Initial fetch on mount
    fetchLiveWorkflow()
  }, [])

  // Auto-play timer
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null
    if (isAutoPlaying) {
      timer = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= 9) {
            setIsAutoPlaying(false)
            return 9
          }
          return prev + 1
        })
      }, 3500)
    }
    return () => {
      if (timer) clearInterval(timer)
    }
  }, [isAutoPlaying])

  // Scroll active section into view when stepping
  useEffect(() => {
    if (viewMode === 'progressive' && sectionRefs.current[currentStep - 1]) {
      sectionRefs.current[currentStep - 1]?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    }
  }, [currentStep, viewMode])

  // Handlers for step actions
  const handleAnalyze = async () => {
    await fetchLiveWorkflow()
    setCurrentStep(2)
  }

  const handleProceedToPlan = () => {
    setCurrentStep(3)
  }

  const handleApplySnapshot = () => {
    setCurrentStep(4)
  }

  const handleAdvanceToCritic = () => {
    setCurrentStep(5)
  }

  const handleRemediate = () => {
    setCurrentStep(6)
  }

  const handleAdvanceToFinal = () => {
    setCurrentStep(7)
  }

  const handleAdvanceToAfp = () => {
    setCurrentStep(8)
  }

  const handleAdvanceToEvidence = () => {
    setCurrentStep(9)
  }

  const handleReset = () => {
    setCurrentStep(1)
    setIsAutoPlaying(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Determine whether each section is visible
  const isVisible = (stepNumber: number) => {
    if (viewMode === 'all') return true
    return currentStep >= stepNumber
  }

  const stageTitles: Record<number, string> = {
    1: 'Change Request & Field Definition',
    2: 'Blast Radius Topology (9 Artifacts Discovered)',
    3: 'Topological Change Plan & Semantic Mutations',
    4: 'Snapshot 2 Deterministic Validation (DATA_TRUNCATION Caught)',
    5: 'Adversarial Critic Audit (Planted Variable Mismatch)',
    6: 'Autonomous Working-Storage Remediation',
    7: 'Final Certification & Verification (PASS & 0 Findings)',
    8: 'Downstream AFP Print Stream Presentation',
    9: 'Tamper-Evident SHA-256 Audit Trail & Cryptographic Seal',
  }

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Enterprise Navigation Header */}
      <Header
        currentStep={currentStep}
        totalSteps={9}
        onStepSelect={(step) => {
          setIsAutoPlaying(false)
          setCurrentStep(step)
        }}
        onPrev={() => {
          setIsAutoPlaying(false)
          setCurrentStep((prev) => Math.max(1, prev - 1))
        }}
        onNext={() => {
          setIsAutoPlaying(false)
          setCurrentStep((prev) => Math.min(9, prev + 1))
        }}
        isAutoPlaying={isAutoPlaying}
        onToggleAutoPlay={() => setIsAutoPlaying(!isAutoPlaying)}
        onReset={handleReset}
        isRunningWorkflow={isLoading}
      />

      {/* Main Workspace Stage */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-7 sm:px-6 lg:px-8 space-y-6">
        {/* Executive Platform Summary / Telemetry Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-[#0b1222] border border-slate-800 rounded-lg p-3.5 shadow-sm">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              Blast Radius
            </span>
            <div className="font-mono text-lg font-bold text-white mt-1">
              9 <span className="text-xs text-slate-400 font-normal">Artifacts</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Topological Scope</span>
          </div>

          <div className="bg-[#0b1222] border border-slate-800 rounded-lg p-3.5 shadow-sm">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              Dependencies
            </span>
            <div className="font-mono text-lg font-bold text-blue-300 mt-1">
              20 <span className="text-xs text-slate-400 font-normal">Edges</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Call & Copybook Graph</span>
          </div>

          <div className="bg-[#0b1222] border border-slate-800 rounded-lg p-3.5 shadow-sm">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              Data Lineage
            </span>
            <div className="font-mono text-lg font-bold text-indigo-300 mt-1">
              6 <span className="text-xs text-slate-400 font-normal">Tiers</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Schema → Storage → Print</span>
          </div>

          <div className="bg-[#0b1222] border border-slate-800 rounded-lg p-3.5 shadow-sm">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              Validation Pass 1
            </span>
            <div className="font-mono text-lg font-bold text-red-400 mt-1">
              FAIL
            </div>
            <span className="text-[10px] text-red-400/80 font-mono block mt-0.5 truncate">
              DATA_TRUNCATION
            </span>
          </div>

          <div className="bg-[#0b1222] border border-slate-800 rounded-lg p-3.5 shadow-sm">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              Critic Finding
            </span>
            <div className="font-mono text-lg font-bold text-amber-300 mt-1">
              1 <span className="text-xs text-slate-400 font-normal">Critical</span>
            </div>
            <span className="text-[10px] text-amber-400/80 font-mono block mt-0.5 truncate">
              WS-ACCT-CUST-ID X(8)
            </span>
          </div>

          <div className="bg-[#0b1222] border border-slate-800 rounded-lg p-3.5 shadow-sm">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              Certification
            </span>
            <div className="font-mono text-lg font-bold text-emerald-400 mt-1 flex items-center gap-1.5">
              <span>PASS</span>
              <span className="text-[11px] text-emerald-500 font-normal">✓</span>
            </div>
            <span className="text-[10px] text-emerald-400/80 font-mono block mt-0.5">
              0 Inconsistencies
            </span>
          </div>
        </div>

        {/* View Mode & Active Stage Bar */}
        <div className="bg-[#0b1222] border border-slate-800 rounded-xl px-5 py-3 flex flex-wrap items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Current Stage:
            </span>
            <span className="font-mono text-sm font-semibold text-slate-200">
              {stageTitles[currentStep] || 'Workflow Execution'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-mono mr-1">View Mode:</span>
            <div className="flex items-center rounded-lg border border-slate-700/80 bg-slate-900 p-0.5">
              <button
                onClick={() => setViewMode('progressive')}
                className={`text-xs px-3 py-1 rounded-md font-mono transition-colors ${
                  viewMode === 'progressive'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Sequential
              </button>
              <button
                onClick={() => setViewMode('all')}
                className={`text-xs px-3 py-1 rounded-md font-mono transition-colors ${
                  viewMode === 'all'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Full Overview
              </button>
            </div>
          </div>
        </div>

        {/* 1. CHANGE REQUEST HERO */}
        {isVisible(1) && (
          <div ref={(el) => (sectionRefs.current[0] = el)} className="transition-all duration-300">
            <ChangeRequestCard
              data={workflowData}
              onAnalyze={handleAnalyze}
              isLoading={isLoading}
              isCompleted={currentStep > 1}
            />
          </div>
        )}

        {/* 2. IMPACT GRAPH (BLAST RADIUS) */}
        {isVisible(2) && (
          <div ref={(el) => (sectionRefs.current[1] = el)} className="transition-all duration-300">
            <ImpactGraphView
              impacted={workflowData.impacted_artifacts}
              onProceed={handleProceedToPlan}
            />
          </div>
        )}

        {/* 3. CHANGE PLAN */}
        {isVisible(3) && (
          <div ref={(el) => (sectionRefs.current[2] = el)} className="transition-all duration-300">
            <ChangePlanView
              proposals={workflowData.initial_proposals}
              onApplySnapshot={handleApplySnapshot}
              isApplied={currentStep >= 4}
              snapshotId="snapshot-2"
            />
          </div>
        )}

        {/* 4. VALIDATION FAIL */}
        {isVisible(4) && (
          <div ref={(el) => (sectionRefs.current[3] = el)} className="transition-all duration-300">
            <ValidationCard
              validation={workflowData.first_validation}
              snapshotName="Snapshot 2"
              onAdvanceToCritic={handleAdvanceToCritic}
            />
          </div>
        )}

        {/* 5. ADVERSARIAL CRITIC REVIEW */}
        {isVisible(5) && (
          <div ref={(el) => (sectionRefs.current[4] = el)} className="transition-all duration-300">
            <AdversarialCriticCard
              findings={workflowData.adversarial_findings}
              remediationProposal={workflowData.remediation_proposal}
              onRemediate={handleRemediate}
              isRemediated={currentStep >= 6}
            />
          </div>
        )}

        {/* 6. REMEDIATION DETAILS */}
        {isVisible(6) && currentStep === 6 && (
          <div ref={(el) => (sectionRefs.current[5] = el)} className="bg-[#0b1222] border border-blue-500/40 rounded-xl p-6 shadow-xl relative overflow-hidden transition-all duration-300">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                  <span className="text-[11px] uppercase tracking-wider text-blue-400 font-mono font-bold">
                    SNAPSHOT 3 REMEDIATION
                  </span>
                </div>
                <h3 className="text-lg font-mono font-bold text-white">
                  Remediation Patch Applied to Working-Storage
                </h3>
                <p className="text-xs text-slate-300 mt-1 max-w-2xl font-mono">
                  `cobol/ACCTPROG.CBL`: WS-ACCT-CUST-ID resized PIC X(8) &rarr; PIC X(12). Clean snapshot branch created under `snapshots/snapshot-3`.
                </p>
              </div>

              <button
                onClick={handleAdvanceToFinal}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold uppercase tracking-wider shadow-lg shadow-emerald-950/40 transition-all border border-emerald-400/30 active:scale-95"
              >
                <span>RE-VALIDATE SNAPSHOT 3</span>
                <span>&rarr;</span>
              </button>
            </div>
          </div>
        )}

        {/* 7. FINAL VERIFICATION */}
        {isVisible(7) && (
          <div ref={(el) => (sectionRefs.current[6] = el)} className="transition-all duration-300">
            <FinalVerificationCard
              status={workflowData.final_validation.status}
              snapshotName="Snapshot 3"
              deterministicValidation={workflowData.second_validation.status}
              adversarialFindingsCount={0}
              evidenceGenerated={true}
              afpInspected={true}
              onNext={handleAdvanceToAfp}
            />
          </div>
        )}

        {/* 8. AFP OUTPUT IMPACT */}
        {isVisible(8) && (
          <div ref={(el) => (sectionRefs.current[7] = el)} className="transition-all duration-300">
            <AfpImpactCard
              afpImpact={workflowData.afp_impact}
              onNext={handleAdvanceToEvidence}
            />
          </div>
        )}

        {/* 9. EVIDENCE REPORT */}
        {isVisible(9) && (
          <div ref={(el) => (sectionRefs.current[8] = el)} className="transition-all duration-300">
            <EvidenceReportCard
              reportPath={workflowData.evidence_report}
              hashes={workflowData.deterministic_hashes}
            />
          </div>
        )}
      </main>

      {/* Enterprise Footer */}
      <footer className="mt-16 border-t border-slate-800/80 bg-[#05080f] py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            Z-FORGE &bull; IBM Bob 2.0 Hackathon &bull; AI Change Engineering for IBM Z
          </div>
          <div className="text-slate-400">
            Deterministic Engine: Python 3.11+ &bull; Immutable Snapshots &bull; RFC-6962 SHA-256 Hashing
          </div>
        </div>
      </footer>
    </div>
  )
}
