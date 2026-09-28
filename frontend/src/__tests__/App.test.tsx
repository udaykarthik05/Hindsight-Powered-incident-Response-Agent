import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { App } from "../App";
import { api } from "../api/client";
import { BackendHealth, HindsightConnectionStatus, Incident, InvestigationResult } from "../types";

vi.mock("../api/client", () => ({
  api: {
    getHealth: vi.fn(),
    getHindsightStatus: vi.fn(),
    getIncidents: vi.fn(),
    investigateIncident: vi.fn(),
    createIncident: vi.fn(),
    resolveIncident: vi.fn(),
  },
}));

const mockIncidents: Incident[] = [
  {
    incident_id: "INC-2025-101",
    title: "Auth Service Database Connection Pool Exhaustion",
    description: "504 Gateway Timeouts during morning peak",
    severity: "critical",
    affected_service: "auth-service",
    timestamp: "2025-10-14T08:15:00Z",
    logs: ["Connection pool exhausted"],
    error_messages: ["psycopg2.OperationalError"],
    status: "open",
    created_at: "2025-10-14T08:20:00Z",
  },
];

const mockInvestigationResult: InvestigationResult = {
  incident_id: "INC-2025-101",
  summary: "Database connection pool exhausted under concurrent load.",
  observed_signals: {
    affected_service: "auth-service",
    error_types: ["OperationalError"],
    infrastructure_components: ["connection_pool"],
    suspected_categories: ["database"],
    deployment_correlated: false,
    extracted_keywords: ["pool"],
  },
  historical_context: {
    available: false,
    query_used: "auth-service pool",
    recalled_incidents: [],
    status_message: "Hindsight offline.",
  },
  hypotheses: [
    {
      hypothesis: "Connection leak in unclosed session",
      supporting_evidence: ["pool full"],
      contradicting_evidence: [],
      related_historical_incidents: [],
      confidence: 0.85,
    },
  ],
  investigation_steps: [
    {
      step_number: 1,
      action: "Check open connections count",
      rationale: "Verify leakage",
      target_system: "PostgreSQL",
    },
  ],
  remediation_recommendations: {
    immediate_mitigation: ["Restart pods to reclaim slots"],
    long_term_fix: ["Wrap db session in context manager"],
  },
  confidence: 0.85,
  limitations: ["Hindsight offline"],
  generated_at: "2025-10-14T08:30:00Z",
};

const mockHealth: BackendHealth = {
  status: "ok",
  app: "Incident Response Agent",
  environment: "development",
  timestamp: "2026-09-28T00:00:00Z",
};

const mockHindsightOffline: HindsightConnectionStatus = {
  connected: false,
  base_url: "http://localhost:8888",
  bank_id: "incident-response-bank",
  message: "Hindsight service unreachable.",
};

describe("App Dashboard Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and displays incidents on successful backend connection", async () => {
    vi.mocked(api.getHealth).mockResolvedValue(mockHealth);
    vi.mocked(api.getHindsightStatus).mockResolvedValue(mockHindsightOffline);
    vi.mocked(api.getIncidents).mockResolvedValue(mockIncidents);

    render(<App />);

    expect(screen.getByText(/loading incidents from backend/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText("INC-2025-101").length).toBeGreaterThanOrEqual(1);
      expect(
        screen.getByRole("heading", { level: 1, name: "Auth Service Database Connection Pool Exhaustion" })
      ).toBeInTheDocument();
    });

    expect(screen.getByText("API: Online")).toBeInTheDocument();
    expect(screen.getByText("Hindsight: Offline")).toBeInTheDocument();
  });

  it("displays backend offline banner when API call fails", async () => {
    vi.mocked(api.getHealth).mockRejectedValue(
      new Error("Failed to connect to backend server. Is FastAPI running on http://127.0.0.1:8000?")
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/backend disconnected:/i)).toBeInTheDocument();
      expect(screen.getByText(/retry connection/i)).toBeInTheDocument();
    });
  });

  it("handles investigation flow successfully", async () => {
    vi.mocked(api.getHealth).mockResolvedValue(mockHealth);
    vi.mocked(api.getHindsightStatus).mockResolvedValue(mockHindsightOffline);
    vi.mocked(api.getIncidents).mockResolvedValue(mockIncidents);
    vi.mocked(api.investigateIncident).mockResolvedValue(mockInvestigationResult);

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("INC-2025-101").length).toBeGreaterThanOrEqual(1);
    });

    const investigateBtn = screen.getByRole("button", { name: /investigate incident/i });
    fireEvent.click(investigateBtn);

    await waitFor(() => {
      expect(screen.getByText(/executive investigation summary/i)).toBeInTheDocument();
      expect(
        screen.getByText("Database connection pool exhausted under concurrent load.")
      ).toBeInTheDocument();
    });
  });

  it("displays investigation failure message when backend returns an error", async () => {
    vi.mocked(api.getHealth).mockResolvedValue(mockHealth);
    vi.mocked(api.getHindsightStatus).mockResolvedValue(mockHindsightOffline);
    vi.mocked(api.getIncidents).mockResolvedValue(mockIncidents);
    vi.mocked(api.investigateIncident).mockRejectedValue(
      new Error("Analysis pipeline failed: timeout awaiting synthesis")
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("INC-2025-101").length).toBeGreaterThanOrEqual(1);
    });

    const investigateBtn = screen.getByRole("button", { name: /investigate incident/i });
    fireEvent.click(investigateBtn);

    await waitFor(() => {
      expect(screen.getByText(/investigation pipeline failed/i)).toBeInTheDocument();
      expect(
        screen.getByText("Analysis pipeline failed: timeout awaiting synthesis")
      ).toBeInTheDocument();
    });
  });
});
