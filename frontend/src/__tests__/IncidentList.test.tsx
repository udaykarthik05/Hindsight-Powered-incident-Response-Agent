import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { IncidentList } from "../components/IncidentList";
import { Incident } from "../types";

const mockIncidents: Incident[] = [
  {
    incident_id: "INC-2025-101",
    title: "Payment Gateway Connection Timeouts",
    description: "Checkout service failing with 504 Gateway Timeout",
    severity: "critical",
    affected_service: "payment-service",
    timestamp: "2025-10-15T14:30:00Z",
    logs: ["Connection pool exhausted: active=50/50"],
    error_messages: ["ConnectionTimeoutError"],
    status: "open",
    created_at: "2025-10-15T14:30:00Z",
  },
  {
    incident_id: "INC-2025-102",
    title: "Auth Token Validation Spike",
    description: "JWT verification latency elevated",
    severity: "medium",
    affected_service: "auth-service",
    timestamp: "2025-10-14T10:00:00Z",
    logs: ["JWK set refresh failed"],
    error_messages: ["KeyFetchTimeout"],
    status: "resolved",
    created_at: "2025-10-14T10:00:00Z",
    resolved_at: "2025-10-14T11:00:00Z",
  },
];

describe("IncidentList Component", () => {
  it("renders incident list items with title, service, and badges", () => {
    const onSelect = vi.fn();
    render(
      <IncidentList
        incidents={mockIncidents}
        selectedId="INC-2025-101"
        onSelect={onSelect}
        loading={false}
      />
    );

    expect(screen.getByText("INC-2025-101")).toBeInTheDocument();
    expect(screen.getByText("Payment Gateway Connection Timeouts")).toBeInTheDocument();
    expect(screen.getByText("payment-service")).toBeInTheDocument();

    expect(screen.getByText("INC-2025-102")).toBeInTheDocument();
    expect(screen.getByText("Auth Token Validation Spike")).toBeInTheDocument();
    expect(screen.getByText("auth-service")).toBeInTheDocument();
  });

  it("filters incidents by search term", () => {
    render(
      <IncidentList
        incidents={mockIncidents}
        selectedId={null}
        onSelect={vi.fn()}
        loading={false}
      />
    );

    const searchInput = screen.getByPlaceholderText(/search by id, title, service/i);
    fireEvent.change(searchInput, { target: { value: "payment" } });

    expect(screen.getByText("Payment Gateway Connection Timeouts")).toBeInTheDocument();
    expect(screen.queryByText("Auth Token Validation Spike")).not.toBeInTheDocument();
  });

  it("filters incidents by status dropdown", () => {
    render(
      <IncidentList
        incidents={mockIncidents}
        selectedId={null}
        onSelect={vi.fn()}
        loading={false}
      />
    );

    const statusSelect = screen.getByDisplayValue("All Status");
    fireEvent.change(statusSelect, { target: { value: "open" } });

    expect(screen.getByText("INC-2025-101")).toBeInTheDocument();
    expect(screen.queryByText("INC-2025-102")).not.toBeInTheDocument();
  });

  it("calls onSelect when an incident card is clicked", () => {
    const onSelect = vi.fn();
    render(
      <IncidentList
        incidents={mockIncidents}
        selectedId={null}
        onSelect={onSelect}
        loading={false}
      />
    );

    const card = screen.getByText("Payment Gateway Connection Timeouts");
    fireEvent.click(card);

    expect(onSelect).toHaveBeenCalledWith("INC-2025-101");
  });

  it("shows loading state when loading is true", () => {
    render(
      <IncidentList
        incidents={[]}
        selectedId={null}
        onSelect={vi.fn()}
        loading={true}
      />
    );

    expect(screen.getByText(/loading incidents from backend/i)).toBeInTheDocument();
  });

  it("shows empty state when no incidents match filter", () => {
    render(
      <IncidentList
        incidents={mockIncidents}
        selectedId={null}
        onSelect={vi.fn()}
        loading={false}
      />
    );

    const searchInput = screen.getByPlaceholderText(/search by id, title, service/i);
    fireEvent.change(searchInput, { target: { value: "nonexistent-query-xyz" } });

    expect(screen.getByText(/no incidents found/i)).toBeInTheDocument();
  });
});
