export interface ObservedSignals {
  affected_service: string;
  error_types: string[];
  infrastructure_components: string[];
  suspected_categories: string[];
  deployment_correlated: boolean;
  extracted_keywords: string[];
}

export interface HistoricalIncidentMatch {
  incident_id: string;
  title: string;
  service: string;
  similarity_score?: number | null;
  summary: string;
  tags: string[];
}

export interface HistoricalContext {
  available: boolean;
  query_used: string;
  recalled_incidents: HistoricalIncidentMatch[];
  reflection_summary?: string | null;
  status_message: string;
}

export interface Hypothesis {
  hypothesis: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  related_historical_incidents: string[];
  confidence: number;
}

export interface InvestigationStep {
  step_number: number;
  action: string;
  rationale: string;
  target_system: string;
}

export interface RemediationPlan {
  immediate_mitigation: string[];
  long_term_fix: string[];
}

export interface InvestigationResult {
  incident_id: string;
  summary: string;
  observed_signals: ObservedSignals;
  historical_context: HistoricalContext;
  hypotheses: Hypothesis[];
  investigation_steps: InvestigationStep[];
  remediation_recommendations: RemediationPlan;
  confidence: number;
  limitations: string[];
  reasoning_mode?: "llm" | "heuristic_fallback";
  llm_provider?: string | null;
  llm_model?: string | null;
  generated_at: string;
}
