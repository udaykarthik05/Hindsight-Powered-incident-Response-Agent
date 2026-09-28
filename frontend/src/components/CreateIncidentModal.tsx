import React, { useState } from "react";
import { X } from "lucide-react";
import { IncidentCreate, Severity } from "../types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: IncidentCreate) => Promise<void>;
}

export const CreateIncidentModal: React.FC<Props> = ({ isOpen, onClose, onSubmit }) => {
  const [title, setTitle] = useState("");
  const [service, setService] = useState("");
  const [severity, setSeverity] = useState<Severity>("high");
  const [description, setDescription] = useState("");
  const [logsText, setLogsText] = useState("");
  const [errorText, setErrorText] = useState("");
  const [customId, setCustomId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !service.trim() || !description.trim()) {
      setError("Please fill in Title, Service, and Description.");
      return;
    }

    setSubmitting(true);
    setError(null);

    const logs = logsText
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    const error_messages = errorText
      .split("\n")
      .map((e) => e.trim())
      .filter(Boolean);

    try {
      await onSubmit({
        title: title.trim(),
        affected_service: service.trim(),
        severity,
        description: description.trim(),
        logs,
        error_messages,
        incident_id: customId.trim() || undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to create incident");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-window">
        <div className="modal-header">
          <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)" }}>
            Report New Incident
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
              <label className="form-label">Incident Title *</label>
              <input
                className="form-input"
                placeholder="e.g. Payment Gateway 504 Timeout and Database Latency"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div className="form-group">
                <label className="form-label">Affected Service *</label>
                <input
                  className="form-input"
                  placeholder="e.g. payment-service"
                  value={service}
                  onChange={(e) => setService(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Severity Level *</label>
                <select
                  className="form-select"
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value as Severity)}
                >
                  <option value="critical">CRITICAL</option>
                  <option value="high">HIGH</option>
                  <option value="medium">MEDIUM</option>
                  <option value="low">LOW</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Description & Observed Symptoms *</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Provide a detailed description of observed customer impact and timeline..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Observed Raw Logs (Optional, one per line)</label>
              <textarea
                className="form-textarea"
                rows={3}
                style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}
                placeholder="2026-03-28 14:02:11 ERROR [pool.py:90] Connection is not available..."
                value={logsText}
                onChange={(e) => setLogsText(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Extracted Error Messages (Optional, one per line)</label>
              <textarea
                className="form-textarea"
                rows={2}
                style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}
                placeholder="psycopg2.OperationalError: remaining connection slots are reserved"
                value={errorText}
                onChange={(e) => setErrorText(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Custom Incident ID (Optional)</label>
              <input
                className="form-input"
                placeholder="Leave blank to auto-generate (e.g. INC-2026-001)"
                value={customId}
                onChange={(e) => setCustomId(e.target.value)}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? (
                <>
                  <div className="spinner" />
                  <span>Submitting...</span>
                </>
              ) : (
                <span>Report Incident</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
