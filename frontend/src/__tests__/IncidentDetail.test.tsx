import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { IncidentDetail } from "../components/IncidentDetail";
import { Incident, InvestigationResult } from "../types";

const mockIncident: Incident = {
  incident_id: "INC-2025-101",
  title: "Payment Gateway Connection Timeouts",
  description: "Checkout service failing with 504 Gateway Timeout during peak checkout volume.",
  severity: "critical",
  affected_service: "payment-service",
  timestamp: "2025-10-15T14:30:00Z",
  logs: [
    "2025-10-15T14:30:12Z [ERROR] connection pool exhausted (active=50/50)",
    "2025-10-15T14:30:15Z [WARN] request queue depth exceeded limit (queue=250)",
  ],
  error_messages: ["ConnectionTimeoutError: Client unable to acquire connection within 5000ms"],
  status: "open",
  created_at: "2025-10-15T14:30:00Z",
};

const mockInvestigationResult: InvestigationResult = {
  incident_id: "INC-2025-101",
  summary: "The payment-service experienced connection pool exhaustion leading to gateway timeouts.",
  observed_signals: {
    affected_service: "payment-service",
    error_types: ["ConnectionTimeoutError"],
    infrastructure_components: ["connection_pool"],
    suspected_categories: ["resource_exhaustion"],
    deployment_correlated: false,
    extracted_keywords: ["pool", "timeout"],
  },
  historical_context: {
    available: false,
    query_used: "payment-service ConnectionTimeoutError",
    recalled_incidents: [],
    status_message: "Historical context unavailable — Hindsight service is not connected.",
  },
  hypotheses: [
    {
      hypothesis: "Database connection pool exhausted under concurrent checkout load",
      supporting_evidence: ["active=50/50 connections"],
      contradicting_evidence: [],
      related_historical_incidents: [],
      confidence: 0.85,
    },
  ],
  investigation_steps: [
    {
      step_number: 1,
      action: "Check database connection pool metrics in Grafana",
      rationale: "Confirm whether connection leaks or spike in queries caused starvation",
      target_system: "PostgreSQL Database",
    },
  ],
  remediation_recommendations: {
    immediate_mitigation: ["Increase max_connections pool size from 50 to 100"],
    long_term_fix: ["Implement query timeout and circuit breaker"],
  },
  confidence: 0.85,
  limitations: ["Hindsight offline; analysis heuristic-only"],
  generated_at: "2025-10-15T14:35:00Z",
};

describe("IncidentDetail Component", () => {
  it("shows empty state when no incident is selected", () => {
    render(
      <IncidentDetail
        incident={null}
        investigationResult={null}
        onInvestigate={vi.fn()}
        onResolve={vi.fn()}
        investigating={false}
        investigationError={null}
      />
    );

    expect(screen.getByText(/select an incident to view details/i)).toBeInTheDocument();
  });

  it("renders incident details correctly", () => {
    render(
      <IncidentDetail
        incident={mockIncident}
        investigationResult={null}
        onInvestigate={vi.fn()}
        onResolve={vi.fn()}
        investigating={false}
        investigationError={null}
      />
    );

    expect(screen.getByText("INC-2025-101")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Payment Gateway Connection Timeouts" })).toBeInTheDocument();
    expect(screen.getByText("payment-service")).toBeInTheDocument();
  });

  it("triggers onInvestigate when Investigate button is clicked", () => {
    const onInvestigate = vi.fn();
    render(
      <IncidentDetail
        incident={mockIncident}
        investigationResult={null}
        onInvestigate={onInvestigate}
        onResolve={vi.fn()}
        investigating={false}
        investigationError={null}
      />
    );

    const button = screen.getByRole("button", { name: /investigate incident/i });
    fireEvent.click(button);

    expect(onInvestigate).toHaveBeenCalledWith("INC-2025-101");
  });

  it("displays loading state while investigation is running", () => {
    render(
      <IncidentDetail
        incident={mockIncident}
        investigationResult={null}
        onInvestigate={vi.fn()}
        onResolve={vi.fn()}
        investigating={true}
        investigationError={null}
      />
    );

    expect(screen.getByText(/investigating incident.../i)).toBeInTheDocument();
    expect(screen.getByText(/ai incident response agent running.../i)).toBeInTheDocument();
  });

  it("switches to Overview tab and displays raw telemetry & logs", () => {
    render(
      <IncidentDetail
        incident={mockIncident}
        investigationResult={null}
        onInvestigate={vi.fn()}
        onResolve={vi.fn()}
        investigating={false}
        investigationError={null}
      />
    );

    const overviewTab = screen.getByRole("button", { name: /overview & raw telemetry/i });
    fireEvent.click(overviewTab);

    expect(screen.getByText(/checkout service failing with 504 gateway timeout/i)).toBeInTheDocument();
    expect(screen.getByText(/connection pool exhausted \(active=50\/50\)/i)).toBeInTheDocument();
    expect(screen.getByText(/connectiontimeouterror: client unable to acquire connection/i)).toBeInTheDocument();
  });

  it("renders investigation result when available", () => {
    render(
      <IncidentDetail
        incident={mockIncident}
        investigationResult={mockInvestigationResult}
        onInvestigate={vi.fn()}
        onResolve={vi.fn()}
        investigating={false}
        investigationError={null}
      />
    );

    expect(screen.getByText(/executive investigation summary/i)).toBeInTheDocument();
    expect(screen.getByText(/the payment-service experienced connection pool exhaustion/i)).toBeInTheDocument();
  });

  it("renders investigation error alert when error occurs", () => {
    render(
      <IncidentDetail
        incident={mockIncident}
        investigationResult={null}
        onInvestigate={vi.fn()}
        onResolve={vi.fn()}
        investigating={false}
        investigationError="Backend investigation service timed out after 30s"
      />
    );

    expect(screen.getByText(/investigation pipeline failed/i)).toBeInTheDocument();
    expect(screen.getByText(/backend investigation service timed out after 30s/i)).toBeInTheDocument();
  });
});
