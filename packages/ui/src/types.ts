/**
 * Z-FORGE Change Control Center Types & Default Workflow Data
 */

export interface SemanticChange {
  kind: string
  line: number
  before: string
  after: string
  impact: string
}

export interface Proposal {
  id: string
  artifact_id: string
  description: string
  confidence: number
  status: string
  semantic_changes: SemanticChange[]
}

export interface ImpactedArtifact {
  id: string
  path: string
  type: 'COPYBOOK' | 'COBOL' | 'HLASM' | 'DATASET' | 'JCL' | 'AFP'
  reason: string
  details: string
}

export interface AdversarialFinding {
  severity: string
  artifact: string
  finding_type: string
  evidence: string
  remediation: string
}

export interface ValidationResult {
  status: 'FAIL' | 'PASS'
  finding: string | null
  source_length?: number
  destination_length?: number
  artifact?: string
  scenario_name?: string
}

export interface AfpImpact {
  artifact: string
  document_name: string
  pages_count: number
  total_elements: number
  lineage_path: string[]
  comparison?: {
    before_capacity: number
    after_capacity: number
    source_schema_changed: boolean
    afp_structure_changed: boolean
    afp_layout_changed: boolean
    explanation: string
  }
  visualization_path: string
}

export interface WorkflowResult {
  status: 'PASS' | 'FAIL'
  change_request: {
    field_name?: string
    field?: string
    target_type?: string
    target?: string
    old_length: number
    new_length: number
    description?: string
  }
  impacted_artifacts: ImpactedArtifact[]
  initial_proposals: Proposal[]
  remediation_proposal?: Proposal
  initial_snapshot: string
  remediation_snapshot: string
  first_validation: ValidationResult
  adversarial_findings: AdversarialFinding[]
  second_validation: ValidationResult
  final_validation: {
    status: 'PASS' | 'FAIL'
  }
  evidence_report: string
  deterministic_hashes: Record<string, string>
  afp_impact: AfpImpact
}

export const DEFAULT_WORKFLOW_DATA: WorkflowResult = {
  status: 'PASS',
  change_request: {
    field: 'CUSTOMER-ID',
    field_name: 'CUSTOMER-ID',
    target: 'PIC X(12)',
    target_type: 'PIC X(12)',
    old_length: 8,
    new_length: 12,
    description: 'Expand CUSTOMER-ID from PIC X(8) to PIC X(12)',
  },
  impacted_artifacts: [
    {
      id: '7f1285a5accb3eb9',
      path: 'datasets/CUST.MASTER.FILE.dsd',
      type: 'DATASET',
      reason: 'SCHEMA_DEPENDENCY',
      details: 'Dataset schema contains CUSTOMER-ID',
    },
    {
      id: '819c79ed37e885b3',
      path: 'copybooks/CUSTMAST.CPY',
      type: 'COPYBOOK',
      reason: 'DIRECT_FIELD_REFERENCE',
      details: 'Artifact directly declares or references CUSTOMER-ID',
    },
    {
      id: '310e5d6308a474c1',
      path: 'datasets/CUST.REPORT.FILE.dsd',
      type: 'DATASET',
      reason: 'DATA_LINEAGE',
      details: 'Downstream consumer of ZENITH.CUST.REPORT.FILE which carries CUSTOMER-ID',
    },
    {
      id: '86631093d5f48144',
      path: 'cobol/CUSTPROG.CBL',
      type: 'COBOL',
      reason: 'DIRECT_FIELD_REFERENCE',
      details: 'Artifact directly declares or references CUSTOMER-ID',
    },
    {
      id: 'be52147dba43d85f',
      path: 'copybooks/ACCTMAST.CPY',
      type: 'COPYBOOK',
      reason: 'COPYBOOK_CHAIN',
      details: 'Copies copybooks/CUSTMAST.CPY which contains CUSTOMER-ID',
    },
    {
      id: '48055e92b3d29a31',
      path: 'cobol/CUSTRPT.CBL',
      type: 'COBOL',
      reason: 'DIRECT_FIELD_REFERENCE',
      details: 'Artifact directly declares or references CUSTOMER-ID',
    },
    {
      id: '22c118bdeaf86148',
      path: 'jcl/CUSTRPT.JCL',
      type: 'JCL',
      reason: 'DATA_LINEAGE',
      details: 'Downstream consumer of ZENITH.CUST.MASTER.FILE which carries CUSTOMER-ID',
    },
    {
      id: '3525e4ac7c4334ce',
      path: 'hlasm/CUSTDSCT.ASM',
      type: 'HLASM',
      reason: 'DIRECT_FIELD_REFERENCE',
      details: 'HLASM artifact references CUSTOMER-ID (layout mirror)',
    },
    {
      id: '712753fa8ff1213d',
      path: 'cobol/ACCTPROG.CBL',
      type: 'COBOL',
      reason: 'COPYBOOK_CHAIN',
      details: 'Copies copybooks/ACCTMAST.CPY which copies copybooks/CUSTMAST.CPY',
    },
  ],
  initial_proposals: [
    {
      id: 'prop-1-copybooks-CUSTMAST.CPY',
      artifact_id: 'copybooks/CUSTMAST.CPY',
      description: 'Expand CUSTOMER-ID to PIC X(12)',
      confidence: 1.0,
      status: 'PROPOSED',
      semantic_changes: [
        {
          kind: 'FIELD_RESIZE',
          line: 5,
          before: '       05  CUSTOMER-ID        PIC X(8).',
          after: '       05  CUSTOMER-ID        PIC X(12).',
          impact: 'Field length expanded from 8 to 12 bytes',
        },
      ],
    },
    {
      id: 'prop-2-cobol-CUSTPROG.CBL',
      artifact_id: 'cobol/CUSTPROG.CBL',
      description: 'Expand WS-CUSTOMER-ID to PIC X(12)',
      confidence: 1.0,
      status: 'PROPOSED',
      semantic_changes: [
        {
          kind: 'FIELD_RESIZE',
          line: 25,
          before: '       05  WS-CUSTOMER-ID     PIC X(8).',
          after: '       05  WS-CUSTOMER-ID     PIC X(12).',
          impact: 'Local working storage field length expanded from 8 to 12 bytes',
        },
      ],
    },
    {
      id: 'prop-3-cobol-CUSTRPT.CBL',
      artifact_id: 'cobol/CUSTRPT.CBL',
      description: 'Expand RPT-CUSTOMER-ID to PIC X(12)',
      confidence: 1.0,
      status: 'PROPOSED',
      semantic_changes: [
        {
          kind: 'FIELD_RESIZE',
          line: 28,
          before: '       05  RPT-CUSTOMER-ID    PIC X(8).',
          after: '       05  RPT-CUSTOMER-ID    PIC X(12).',
          impact: 'Report record field length expanded from 8 to 12 bytes',
        },
      ],
    },
  ],
  remediation_proposal: {
    id: 'prop-remediation-cobol-ACCTPROG.CBL',
    artifact_id: 'cobol/ACCTPROG.CBL',
    description: 'Remediate planted failure: Expand WS-ACCT-CUST-ID to PIC X(12)',
    confidence: 1.0,
    status: 'REMEDIATED',
    semantic_changes: [
      {
        kind: 'FIELD_RESIZE',
        line: 28,
        before: '       05  WS-ACCT-CUST-ID    PIC X(8).',
        after: '       05  WS-ACCT-CUST-ID    PIC X(12).',
        impact: 'Remediates data truncation planted in local variable',
      },
    ],
  },
  initial_snapshot: 'snapshot-2-proposed',
  remediation_snapshot: 'snapshot-3-remediated',
  first_validation: {
    status: 'FAIL',
    finding: 'DATA_TRUNCATION',
    source_length: 12,
    destination_length: 8,
    artifact: 'cobol/ACCTPROG.CBL',
    scenario_name: 'customer-id-expansion',
  },
  adversarial_findings: [
    {
      severity: 'CRITICAL',
      artifact: 'cobol/ACCTPROG.CBL',
      finding_type: 'DATA_TRUNCATION',
      evidence: 'CUSTOMER-ID is 12 bytes but WS-ACCT-CUST-ID remains X(8)',
      remediation: 'Change WS-ACCT-CUST-ID to X(12)',
    },
  ],
  second_validation: {
    status: 'PASS',
    finding: null,
    scenario_name: 'customer-id-expansion',
  },
  final_validation: {
    status: 'PASS',
  },
  evidence_report: 'reports/tamper-evident-evidence.json',
  deterministic_hashes: {
    workspace_baseline_sha256: '0d3f67d791233243...',
    'snapshot-1-baseline_sha256': 'bccfd391b082c57e...',
    'snapshot-2-proposed_sha256': 'a224c524ae3ec7f2...',
    'snapshot-3-remediated_sha256': 'e677aaba26d5c3f9...',
    report_sha256: '8d569fcc15bd530d00bd5237d51ddc9efe1eff601bea8e13a56954a1cd99a3f3',
  },
  afp_impact: {
    artifact: 'afp/CUSTRPT.AFP',
    document_name: 'CUSTRPT-DOC',
    pages_count: 1,
    total_elements: 5,
    lineage_path: [
      'CUSTOMER-ID',
      'copybooks/CUSTMAST.CPY',
      'cobol/CUSTRPT.CBL',
      'datasets/CUST.REPORT.FILE.dsd',
      'jcl/CUSTRPT.JCL',
      'afp/CUSTRPT.AFP',
    ],
    comparison: {
      before_capacity: 8,
      after_capacity: 12,
      source_schema_changed: true,
      afp_structure_changed: false,
      afp_layout_changed: false,
      explanation:
        'Upstream schema expands CUSTOMER-ID from 8 to 12 bytes. The static binary CUSTRPT.AFP maintains 8-byte capacity until the batch print generation job (CUSTRPT.JCL) is re-executed.',
    },
    visualization_path: 'reports/afp-custrpt.html',
  },
}
