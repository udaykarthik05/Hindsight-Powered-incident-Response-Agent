import React, { useState } from "react";
import { CheckCircle2, AlertTriangle, Database, X } from "lucide-react";
import { IncidentResolve, IncidentResolveResponse } from "../types";

interface Props {
  isOpen: boolean;
  incidentId: string;
  onClose: () => void;
  onResolve: (payload: IncidentResolve) => Promise<IncidentResolveResponse | void>;
}

export const ResolveModal: React.FC<Props> = ({
  isOpen,
  incidentId,
  onClose,
  onResolve,
}) => {
  const [rootCause, setRootCause] = useState("");
  const [mitigation, setMitigation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resolutionResult, setResolutionResult] = useState<IncidentResolveResponse | null>(null);

  if (!isOpen) return null;

  const handleDismiss = () => {
    setRootCause("");
    setMitigation("");
    setError(null);
    setResolutionResult(null);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rootCause.trim().length < 5 || mitigation.trim().length < 5) {
      setError("Root cause and mitigation must each have at least 5 characters.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const result = await onResolve({
        root_cause: rootCause.trim(),
        mitigation: mitigation.trim(),
      });
      if (result) {
        setResolutionResult(result);
      } else {
        handleDismiss();
      }
    } catch (err: any) {
      setError(err.message || "Failed to resolve incident");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-window">
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", fontWeight: 700 }}>
            <CheckCircle2 size={18} color="#10b981" />
            <span>Resolve Incident {incidentId}</span>
          </div>
          <button className="btn btn-outline" style={{ padding: "4px" }} onClick={handleDismiss}>
            <X size={16} />
          </button>
        </div>

        {resolutionResult ? (
          <div>
            <div className="modal-body" style={{ textAlign: "center", padding: "24px 16px" }}>
              <div
                style={{
                  display: "inline-flex",
                  padding: "12px",
                  background: "rgba(16, 185, 129, 0.12)",
                  borderRadius: "50%",
                  marginBottom: "14px",
                }}
              >
                <CheckCircle2 size={32} color="#10b981" />
              </div>
              <h3 style={{ fontSize: "16px", color: "var(--text-primary)", marginBottom: "16px" }}>
                Incident {incidentId} Successfully Resolved
              </h3>

              <div
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-md)",
                  padding: "16px",
                  textAlign: "left",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "13px" }}>
                  <span style={{ color: "var(--text-muted)" }}>Resolution:</span>
                  <span style={{ color: "#10b981", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
                    <CheckCircle2 size={14} /> Incident resolved
                  </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "13px" }}>
                  <span style={{ color: "var(--text-muted)" }}>Memory Lifecycle:</span>
                  {resolutionResult.memory_status === "retained" ? (
                    <span style={{ color: "var(--hindsight)", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
                      <Database size={14} /> Added to Hindsight
                    </span>
                  ) : resolutionResult.memory_status === "already_retained" ? (
                    <span style={{ color: "var(--hindsight)", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
                      <Database size={14} /> Already in Hindsight
                    </span>
                  ) : (
                    <span style={{ color: "#f59e0b", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
                      <AlertTriangle size={14} /> Historical memory unavailable
                    </span>
                  )}
                </div>

                {resolutionResult.memory_message && (
                  <div
                    style={{
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      borderTop: "1px solid var(--border)",
                      paddingTop: "8px",
                      lineHeight: 1.4,
                    }}
                  >
                    {resolutionResult.memory_message}
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button type="button" className="btn btn-primary" onClick={handleDismiss} style={{ width: "100%" }}>
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {error && (
                <div
                  style={{
                    background: "var(--critical-bg)",
                    border: "1px solid var(--critical-border)",
                    borderRadius: "var(--radius-md)",
                    padding: "8px 12px",
                    fontSize: "12px",
                    color: "var(--critical)",
                  }}
                >
                  {error}
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Confirmed Technical Root Cause *</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Describe what specific failure, bug, or configuration triggered this outage..."
                  value={rootCause}
                  onChange={(e) => setRootCause(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Applied Mitigation & Remediation *</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Detail the steps taken to halt customer impact and restore stability..."
                  value={mitigation}
                  onChange={(e) => setMitigation(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="modal-footer">
              <button type="button" className="btn btn-outline" onClick={handleDismiss} disabled={submitting}>
                Cancel
              </button>
              <button type="submit" className="btn btn-resolve" disabled={submitting}>
                {submitting ? (
                  <>
                    <div className="spinner" />
                    <span>Resolving & Retaining...</span>
                  </>
                ) : (
                  <span>Mark as Resolved</span>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
