import React, { useState } from "react";
import { CheckCircle2, X } from "lucide-react";
import { IncidentResolve } from "../types";

interface Props {
  isOpen: boolean;
  incidentId: string;
  onClose: () => void;
  onResolve: (payload: IncidentResolve) => Promise<void>;
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

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rootCause.trim().length < 5 || mitigation.trim().length < 5) {
      setError("Root cause and mitigation must each have at least 5 characters.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await onResolve({
        root_cause: rootCause.trim(),
        mitigation: mitigation.trim(),
      });
      onClose();
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
          <button className="btn btn-outline" style={{ padding: "4px" }} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

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
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-resolve" disabled={submitting}>
              {submitting ? (
                <>
                  <div className="spinner" />
                  <span>Resolving...</span>
                </>
              ) : (
                <span>Mark as Resolved</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
