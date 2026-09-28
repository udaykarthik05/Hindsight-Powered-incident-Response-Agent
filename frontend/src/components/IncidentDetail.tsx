import React, { useState } from "react";
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Server,
  Sparkles,
  Terminal,
} from "lucide-react";
import { Incident, IncidentResolve, InvestigationResult } from "../types";
import { InvestigationView } from "./InvestigationView";
import { ResolveModal } from "./ResolveModal";
import { SeverityBadge } from "./SeverityBadge";
import { StatusBadge } from "./StatusBadge";

interface Props {
  incident: Incident | null;
  investigationResult: InvestigationResult | null;
  onInvestigate: (id: string) => Promise<void>;
  onResolve: (id: string, payload: IncidentResolve) => Promise<void>;
  investigating: boolean;
  investigationError: string | null;
}

export const IncidentDetail: React.FC<Props> = ({
  incident,
  investigationResult,
  onInvestigate,
  onResolve,
  investigating,
  investigationError,
}) => {
  const [activeTab, setActiveTab] = useState<"investigation" | "overview">("investigation");
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);

  if (!incident) {
    return (
      <div className="detail-panel">
        <div className="empty-state" style={{ flex: 1 }}>
          <Server size={44} className="empty-icon" />
          <h2 style={{ fontSize: "16px", color: "var(--text-primary)", marginBottom: "6px" }}>
            Select an incident to view details
          </h2>
          <p style={{ fontSize: "13px", maxWidth: "380px" }}>
            Choose an incident from the left sidebar to inspect telemetry, error logs, and trigger the
            AI Incident Response Agent.
          </p>
        </div>
      </div>
    );
  }

  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch {
      return isoStr;
    }
  };

  const handleResolveSubmit = async (payload: IncidentResolve) => {
    await onResolve(incident.incident_id, payload);
  };

  return (
    <div className="detail-panel">
      {/* Header */}
      <div className="detail-header">
        <div className="detail-top-row">
          <div className="detail-title-group">
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--text-muted)" }}>
                {incident.incident_id}
              </span>
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
            </div>
            <h1>{incident.title}</h1>
          </div>

          <div className="action-button-group">
            {incident.status !== "resolved" && (
              <button
                className="btn btn-resolve"
                onClick={() => setIsResolveModalOpen(true)}
              >
                <CheckCircle2 size={15} />
                <span>Resolve</span>
              </button>
            )}

            {/* Core Investigate Button */}
            <button
              className="btn btn-primary"
              onClick={() => onInvestigate(incident.incident_id)}
              disabled={investigating}
              style={{ padding: "10px 18px", fontSize: "14px" }}
            >
              {investigating ? (
                <>
                  <div className="spinner" />
                  <span>Investigating Incident...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Investigate Incident</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Metadata Row */}
        <div className="detail-meta-row">
          <div className="meta-item">
            <strong>Service:</strong>
            <span style={{ color: "var(--accent-light)", fontWeight: 600 }}>
              {incident.affected_service}
            </span>
          </div>
          <div className="meta-item">
            <strong>Occurred:</strong>
            <span>{formatDate(incident.timestamp)}</span>
          </div>
          {incident.resolved_at && (
            <div className="meta-item">
              <strong>Resolved:</strong>
              <span style={{ color: "#10b981" }}>{formatDate(incident.resolved_at)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === "investigation" ? "active" : ""}`}
          onClick={() => setActiveTab("investigation")}
        >
          <BrainCircuit size={16} />
          <span>Agent Investigation</span>
          {investigationResult && (
            <span
              style={{
                background: "rgba(56, 189, 248, 0.2)",
                color: "var(--accent-light)",
                borderRadius: "var(--radius-full)",
                padding: "1px 6px",
                fontSize: "10px",
                fontFamily: "var(--font-mono)",
              }}
            >
              Ready
            </span>
          )}
        </button>

        <button
          className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          <FileText size={16} />
          <span>Overview & Raw Telemetry</span>
          <span
            style={{
              background: "var(--bg-card)",
              color: "var(--text-muted)",
              borderRadius: "var(--radius-full)",
              padding: "1px 6px",
              fontSize: "10px",
              fontFamily: "var(--font-mono)",
            }}
          >
            {incident.logs.length} logs
          </span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === "investigation" ? (
          <div>
            {/* Investigation Error */}
            {investigationError && (
              <div
                style={{
                  background: "var(--critical-bg)",
                  border: "1px solid var(--critical-border)",
                  borderRadius: "var(--radius-lg)",
                  padding: "16px 20px",
                  marginBottom: "20px",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "12px",
                }}
              >
                <AlertCircle size={20} color="var(--critical)" style={{ flexShrink: 0, marginTop: "2px" }} />
                <div>
                  <div style={{ fontWeight: 600, color: "var(--critical)", fontSize: "14px" }}>
                    Investigation Pipeline Failed
                  </div>
                  <div style={{ color: "#fecdd3", fontSize: "13px", marginTop: "4px" }}>
                    {investigationError}
                  </div>
                </div>
              </div>
            )}

            {/* Investigating Loading State */}
            {investigating ? (
              <div className="empty-state" style={{ padding: "80px 24px" }}>
                <div
                  className="spinner"
                  style={{ width: "36px", height: "36px", borderWidth: "3px", borderColor: "rgba(56, 189, 248, 0.2)", borderTopColor: "var(--accent-light)", marginBottom: "20px" }}
                />
                <h3 style={{ fontSize: "16px", color: "var(--text-primary)", marginBottom: "8px" }}>
                  AI Incident Response Agent Running...
                </h3>
                <p style={{ fontSize: "13px", maxWidth: "420px", color: "var(--text-secondary)" }}>
                  Analyzing telemetry signatures, querying Hindsight long-term memory, and synthesizing
                  root-cause hypotheses and non-destructive mitigation plans.
                </p>
              </div>
            ) : investigationResult ? (
              <InvestigationView result={investigationResult} />
            ) : (
              <div className="empty-state" style={{ padding: "80px 24px" }}>
                <BrainCircuit size={48} className="empty-icon" />
                <h3 style={{ fontSize: "16px", color: "var(--text-primary)", marginBottom: "6px" }}>
                  No investigation performed yet
                </h3>
                <p style={{ fontSize: "13px", maxWidth: "420px", marginBottom: "20px" }}>
                  Trigger the AI Incident Response Agent to extract deterministic signals, recall matching
                  historical incidents from Hindsight, and produce ranked hypotheses.
                </p>
                <button
                  className="btn btn-primary"
                  onClick={() => onInvestigate(incident.incident_id)}
                >
                  <Sparkles size={16} />
                  <span>Start Investigation Now</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Overview & Telemetry Tab */
          <div>
            {/* Description */}
            <div className="content-section">
              <div className="section-heading">
                <FileText size={16} color="var(--accent-light)" />
                <span>Description & Reported Impact</span>
              </div>
              <p style={{ fontSize: "14px", color: "#e2e8f0", lineHeight: 1.6 }}>
                {incident.description}
              </p>
            </div>

            {/* Resolved Postmortem Findings (if resolved) */}
            {incident.status === "resolved" && (
              <div
                className="content-section"
                style={{
                  borderColor: "rgba(16, 185, 129, 0.3)",
                  background: "rgba(16, 185, 129, 0.04)",
                }}
              >
                <div className="section-heading" style={{ color: "#10b981" }}>
                  <CheckCircle2 size={16} />
                  <span>Confirmed Postmortem Findings</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div>
                    <strong style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Root Cause:
                    </strong>
                    <p style={{ fontSize: "13px", color: "#e2e8f0", marginTop: "2px" }}>
                      {incident.root_cause || "No root cause documented."}
                    </p>
                  </div>
                  <div>
                    <strong style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Applied Mitigation:
                    </strong>
                    <p style={{ fontSize: "13px", color: "#e2e8f0", marginTop: "2px" }}>
                      {incident.mitigation || "No mitigation documented."}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Error Messages */}
            {incident.error_messages.length > 0 && (
              <div className="content-section">
                <div className="section-heading">
                  <AlertCircle size={16} color="#f43f5e" />
                  <span>Extracted Error Messages ({incident.error_messages.length})</span>
                </div>
                <div className="tag-cloud">
                  {incident.error_messages.map((err, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: "rgba(244, 63, 94, 0.08)",
                        border: "1px solid rgba(244, 63, 94, 0.25)",
                        borderRadius: "var(--radius-sm)",
                        padding: "6px 10px",
                        fontSize: "12px",
                        fontFamily: "var(--font-mono)",
                        color: "#fca5a5",
                        width: "100%",
                      }}
                    >
                      {err}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw Logs */}
            <div className="content-section">
              <div className="section-heading">
                <Terminal size={16} color="var(--accent-light)" />
                <span>Observed Raw Logs & Stack Traces ({incident.logs.length})</span>
              </div>
              {incident.logs.length > 0 ? (
                <div className="telemetry-code">
                  {incident.logs.join("\n")}
                </div>
              ) : (
                <div style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                  No raw logs attached to this incident report.
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Resolve Modal */}
      <ResolveModal
        isOpen={isResolveModalOpen}
        incidentId={incident.incident_id}
        onClose={() => setIsResolveModalOpen(false)}
        onResolve={handleResolveSubmit}
      />
    </div>
  );
};
