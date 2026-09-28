export type Severity = "low" | "medium" | "high" | "critical";

export type IncidentStatus = "open" | "investigating" | "resolved";

export type RetentionStatus = "retained" | "retention_failed" | "already_retained" | "not_attempted";

export interface Incident {
  incident_id: string;
  title: string;
  description: string;
  severity: Severity;
  affected_service: string;
  timestamp: string;
  logs: string[];
  error_messages: string[];
  status: IncidentStatus;
  root_cause?: string | null;
  mitigation?: string | null;
  created_at: string;
  resolved_at?: string | null;
  memory_status?: RetentionStatus | null;
  memory_message?: string | null;
}

export interface IncidentResolveResponse extends Incident {
  memory_status: RetentionStatus;
  memory_message?: string | null;
}

export interface IncidentCreate {
  incident_id?: string;
  title: string;
  description: string;
  severity: Severity;
  affected_service: string;
  timestamp?: string;
  logs?: string[];
  error_messages?: string[];
  status?: IncidentStatus;
  root_cause?: string;
  mitigation?: string;
}

export interface IncidentUpdate {
  title?: string;
  description?: string;
  severity?: Severity;
  affected_service?: string;
  status?: IncidentStatus;
  logs?: string[];
  error_messages?: string[];
  root_cause?: string;
  mitigation?: string;
}

export interface IncidentResolve {
  root_cause: string;
  mitigation: string;
  resolved_at?: string;
}
