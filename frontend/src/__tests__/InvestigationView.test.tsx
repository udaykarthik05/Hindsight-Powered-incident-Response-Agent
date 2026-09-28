import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { InvestigationView } from "../components/InvestigationView";
import { InvestigationResult } from "../types";

const mockInvestigationResult: InvestigationResult = {
  incident_id: "INC-2025-101",
  summary: "Database connection exhaustion during flash sale traffic burst.",
  observed_signals: {
    affected_service: "payment-service",
    error_types: ["ConnectionTimeoutError", "OperationalError"],
    infrastructure_components: ["connection_pool", "database"],
    suspected_categories: ["resource_exhaustion", "database"],
    deployment_correlated: true,
    extracted_keywords: ["pool", "timeout", "checkout"],
  },
  historical_context: {
    available: false,
    query_used: "payment-service pool timeout",
    recalled_incidents: [],
    reflection_summary: null,
    status_message: "Hindsight memory service unreachable.",
  },
  hypotheses: [
    {
      hypothesis: "Connection pool capacity exceeded under peak traffic",
      supporting_evidence: [
        "50/50 pool connections saturated",
        "Traffic increased 300% following promo launch",
      ],
      contradicting_evidence: ["Database CPU remained below 40%"],
      related_historical_incidents: ["INC-2024-089"],
      confidence: 0.88,
    },
  ],
  investigation_steps: [
    {
      step_number: 1,
      action: "Inspect pg_stat_activity for lingering open connections",
      rationale: "Determine if connections are idle in transaction or actively executing queries",
      target_system: "PostgreSQL Primary",
    },
    {
      step_number: 2,
      action: "Check pool checkout wait times on payment-service instances",
      rationale: "Confirm bottleneck location before taking remediation action",
      target_system: "payment-service",
    },
  ],
  remediation_recommendations: {
    immediate_mitigation: [
      "Temporarily increase connection pool limit to 100",
      "Enable shed-load rate limiting on /checkout API",
    ],
    long_term_fix: [
      "Audit long-running database transactions",
      "Implement PgBouncer connection pooling layer",
    ],
  },
  confidence: 0.85,
  limitations: [
    "Hindsight memory offline; historical comparisons unavailable",
    "Synthetic telemetry analysis only",
  ],
  generated_at: "2025-10-15T14:40:00Z",
};

describe("InvestigationView Component", () => {
  it("renders executive summary and confidence percentage", () => {
    render(<InvestigationView result={mockInvestigationResult} />);

    expect(screen.getByText(/executive investigation summary/i)).toBeInTheDocument();
    expect(
      screen.getByText("Database connection exhaustion during flash sale traffic burst.")
    ).toBeInTheDocument();
    expect(screen.getByText("Confidence: 85%")).toBeInTheDocument();
  });

  it("renders observed deterministic signals", () => {
    render(<InvestigationView result={mockInvestigationResult} />);

    expect(screen.getByText(/observed signals \(deterministic analysis\)/i)).toBeInTheDocument();
    expect(screen.getByText("connection_pool")).toBeInTheDocument();
    expect(screen.getAllByText("database").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("ConnectionTimeoutError")).toBeInTheDocument();
    expect(screen.getByText("resource_exhaustion")).toBeInTheDocument();
    expect(screen.getByText(/correlates with recent release/i)).toBeInTheDocument();
    expect(screen.getByText("#pool")).toBeInTheDocument();
  });

  it("honestly displays Hindsight OFFLINE status without fabricating historical incidents", () => {
    render(<InvestigationView result={mockInvestigationResult} />);

    expect(screen.getByText("HINDSIGHT OFFLINE")).toBeInTheDocument();
    expect(
      screen.getByText(/historical context unavailable — hindsight memory service is currently disconnected/i)
    ).toBeInTheDocument();
  });

  it("displays recalled incidents and reflections when Hindsight is online", () => {
    const onlineResult: InvestigationResult = {
      ...mockInvestigationResult,
      historical_context: {
        available: true,
        query_used: "payment-service connection timeout",
        recalled_incidents: [
          {
            incident_id: "INC-2024-042",
            title: "Black Friday Checkout Outage",
            service: "payment-service",
            similarity_score: 0.92,
            summary: "Exhausted PostgreSQL max_connections during flash sale",
            tags: ["database", "pool", "scaling"],
          },
        ],
        reflection_summary:
          "Both incidents share identical pool exhaustion patterns following surge events.",
        status_message: "Recalled 1 matching historical incident from Hindsight.",
      },
    };

    render(<InvestigationView result={onlineResult} />);

    expect(screen.getByText("HINDSIGHT ONLINE")).toBeInTheDocument();
    expect(screen.getByText(/INC-2024-042 — Black Friday Checkout Outage/i)).toBeInTheDocument();
    expect(screen.getByText(/Both incidents share identical pool exhaustion patterns/i)).toBeInTheDocument();
  });

  it("renders hypotheses clearly labeled as hypotheses with evidence", () => {
    render(<InvestigationView result={mockInvestigationResult} />);

    expect(screen.getByText(/ranked root-cause hypotheses/i)).toBeInTheDocument();
    expect(
      screen.getByText("* Hypotheses require empirical verification; not confirmed root causes")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Connection pool capacity exceeded under peak traffic")
    ).toBeInTheDocument();
    expect(screen.getByText("88% Confidence")).toBeInTheDocument();
    expect(screen.getByText("50/50 pool connections saturated")).toBeInTheDocument();
    expect(screen.getByText("Database CPU remained below 40%")).toBeInTheDocument();
    expect(screen.getByText("INC-2024-089")).toBeInTheDocument();
  });

  it("renders ordered diagnostic investigation steps", () => {
    render(<InvestigationView result={mockInvestigationResult} />);

    expect(
      screen.getByText(/recommended non-destructive diagnostic steps/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("Inspect pg_stat_activity for lingering open connections")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Check pool checkout wait times on payment-service instances")
    ).toBeInTheDocument();
  });

  it("renders immediate mitigations and long-term recommendations", () => {
    render(<InvestigationView result={mockInvestigationResult} />);

    expect(screen.getByText(/immediate mitigation \(stop impact\)/i)).toBeInTheDocument();
    expect(
      screen.getByText("Temporarily increase connection pool limit to 100")
    ).toBeInTheDocument();

    expect(screen.getByText(/long-term fixes \(prevent recurrence\)/i)).toBeInTheDocument();
    expect(
      screen.getByText("Implement PgBouncer connection pooling layer")
    ).toBeInTheDocument();
  });

  it("displays investigation caveats and limitations", () => {
    render(<InvestigationView result={mockInvestigationResult} />);

    expect(screen.getByText(/investigation caveats:/i)).toBeInTheDocument();
    expect(
      screen.getByText(/hindsight memory offline; historical comparisons unavailable/i)
    ).toBeInTheDocument();
  });
});
