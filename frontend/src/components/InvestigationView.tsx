import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  GitBranch,
  HelpCircle,
  Lightbulb,
  Search,
  Terminal,
  Wrench,
} from "lucide-react";
import { InvestigationResult } from "../types";

interface Props {
  result: InvestigationResult;
}

export const InvestigationView: React.FC<Props> = ({ result }) => {
  const {
    summary,
    observed_signals,
    historical_context,
    hypotheses,
    investigation_steps,
    remediation_recommendations,
    confidence,
    limitations,
  } = result;

  return (
    <div className="investigation-container">
      {/* 1. Executive Summary */}
      <div className="summary-banner">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "10px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              color: "var(--accent-light)",
              fontWeight: 600,
              fontSize: "13px",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            <Lightbulb size={18} />
            <span>Executive Investigation Summary</span>
          </div>

          <div className="confidence-pill" style={{ fontSize: "12px", padding: "4px 10px" }}>
            Confidence: {(confidence * 100).toFixed(0)}%
          </div>
        </div>

        <p className="summary-text">{summary}</p>
      </div>

      {/* 2. Observed Signals (Deterministic Telemetry Analysis) */}
      <div className="content-section">
        <div className="section-heading">
          <Terminal size={16} color="var(--accent-light)" />
          <span>Observed Signals (Deterministic Analysis)</span>
        </div>

        <div className="signals-grid">
          {/* Affected Subsystems */}
          <div className="signal-card">
            <div className="signal-label">Subsystems Involved</div>
            <div className="tag-cloud">
              {observed_signals.infrastructure_components.length > 0 ? (
                observed_signals.infrastructure_components.map((comp) => (
                  <span key={comp} className="tag-item">
                    {comp}
                  </span>
                ))
              ) : (
                <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                  None isolated
                </span>
              )}
            </div>
          </div>

          {/* Classified Error Types */}
          <div className="signal-card">
            <div className="signal-label">Classified Error Patterns</div>
            <div className="tag-cloud">
              {observed_signals.error_types.length > 0 ? (
                observed_signals.error_types.map((err) => (
                  <span
                    key={err}
                    className="tag-item"
                    style={{ borderColor: "rgba(244, 63, 94, 0.4)", color: "#f87171" }}
                  >
                    {err}
                  </span>
                ))
              ) : (
                <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                  None detected
                </span>
              )}
            </div>
          </div>

          {/* Suspected Categories */}
          <div className="signal-card">
            <div className="signal-label">Suspected Outage Categories</div>
            <div className="tag-cloud">
              {observed_signals.suspected_categories.map((cat) => (
                <span
                  key={cat}
                  className="tag-item"
                  style={{ borderColor: "rgba(250, 204, 21, 0.4)", color: "#fde047" }}
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>

          {/* Deployment Correlation */}
          <div className="signal-card">
            <div className="signal-label">Deployment Correlated</div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <GitBranch
                size={16}
                color={observed_signals.deployment_correlated ? "#f97316" : "var(--text-muted)"}
              />
              <span
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  color: observed_signals.deployment_correlated
                    ? "#f97316"
                    : "var(--text-secondary)",
                }}
              >
                {observed_signals.deployment_correlated
                  ? "YES — Correlates with recent release"
                  : "NO — No deployment keywords detected"}
              </span>
            </div>
          </div>
        </div>

        {/* Salient Technical Keywords */}
        {observed_signals.extracted_keywords.length > 0 && (
          <div style={{ marginTop: "14px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
              Extracted Signal Keywords:
            </span>
            <div className="tag-cloud" style={{ marginTop: "6px" }}>
              {observed_signals.extracted_keywords.map((kw) => (
                <span key={kw} className="tag-item" style={{ background: "rgba(255,255,255,0.04)" }}>
                  #{kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 3. Hindsight Historical Memory Context */}
      <div className="hindsight-box">
        <div className="hindsight-header">
          <div className="hindsight-title">
            <Database size={16} />
            <span>Hindsight Historical Memory Context</span>
          </div>

          <span
            className={`memory-status-badge ${
              historical_context.available ? "memory-online" : "memory-offline"
            }`}
          >
            {historical_context.available ? "HINDSIGHT ONLINE" : "HINDSIGHT OFFLINE"}
          </span>
        </div>

        <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "12px", fontFamily: "var(--font-mono)" }}>
          Query: "{historical_context.query_used}"
        </div>

        {/* Status Message */}
        <div
          style={{
            fontSize: "13px",
            color: historical_context.available ? "#cbd5e1" : "#fda4af",
            marginBottom: "14px",
            padding: "8px 12px",
            background: historical_context.available ? "rgba(168, 85, 247, 0.08)" : "rgba(244, 63, 94, 0.08)",
            border: `1px solid ${historical_context.available ? "rgba(168, 85, 247, 0.2)" : "rgba(244, 63, 94, 0.2)"}`,
            borderRadius: "var(--radius-md)",
          }}
        >
          {historical_context.available
            ? historical_context.status_message
            : "Historical context unavailable — Hindsight memory service is currently disconnected. Investigation based solely on current telemetry."}
        </div>

        {/* Recalled Incidents */}
        {historical_context.available && historical_context.recalled_incidents.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)" }}>
              Recalled Previous Incidents ({historical_context.recalled_incidents.length}):
            </span>
            {historical_context.recalled_incidents.map((match) => (
              <div
                key={match.incident_id}
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-md)",
                  padding: "10px 14px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--hindsight)", fontWeight: 600 }}>
                    {match.incident_id} — {match.title}
                  </span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    Service: {match.service}
                  </span>
                </div>
                <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                  {match.summary}
                </p>
                {match.tags.length > 0 && (
                  <div className="tag-cloud" style={{ marginTop: "6px" }}>
                    {match.tags.map((tag) => (
                      <span key={tag} className="tag-item" style={{ fontSize: "10px" }}>
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Reflection Output */}
        {historical_context.available && historical_context.reflection_summary && (
          <div style={{ marginTop: "14px", borderTop: "1px solid rgba(168, 85, 247, 0.2)", paddingTop: "12px" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--hindsight)" }}>
              Hindsight REFLECT Comparative Synthesis:
            </span>
            <p style={{ fontSize: "13px", color: "#e2e8f0", marginTop: "4px", lineHeight: 1.5 }}>
              {historical_context.reflection_summary}
            </p>
          </div>
        )}
      </div>

      {/* 4. Ranked Hypotheses */}
      <div className="content-section">
        <div className="section-heading">
          <HelpCircle size={16} color="var(--accent-light)" />
          <span>Ranked Root-Cause Hypotheses</span>
          <span style={{ fontSize: "11px", fontWeight: 400, color: "var(--text-muted)", marginLeft: "auto" }}>
            * Hypotheses require empirical verification; not confirmed root causes
          </span>
        </div>

        <div className="hypothesis-list">
          {hypotheses.map((h, i) => (
            <div key={i} className="hypothesis-card">
              <div className="hypothesis-header">
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "12px", fontFamily: "var(--font-mono)", color: "var(--accent-light)", fontWeight: 700 }}>
                    #{i + 1}
                  </span>
                  <span className="hypothesis-title">{h.hypothesis}</span>
                </div>
                <span className="confidence-pill">
                  {(h.confidence * 100).toFixed(0)}% Confidence
                </span>
              </div>

              {/* Supporting Evidence */}
              <div className="evidence-block">
                <strong>Supporting Evidence:</strong>
                <ul className="evidence-list">
                  {h.supporting_evidence.map((ev, idx) => (
                    <li key={idx} style={{ color: "#cbd5e1" }}>
                      {ev}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Contradicting Evidence */}
              {h.contradicting_evidence.length > 0 && (
                <div className="evidence-block" style={{ marginTop: "6px" }}>
                  <strong style={{ color: "#fca5a5" }}>Contradicting / Counter Evidence:</strong>
                  <ul className="evidence-list">
                    {h.contradicting_evidence.map((ev, idx) => (
                      <li key={idx} style={{ color: "#fecdd3" }}>
                        {ev}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Related Historical Incidents */}
              {h.related_historical_incidents.length > 0 && (
                <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
                    Historical Precedent:
                  </span>
                  <div className="tag-cloud">
                    {h.related_historical_incidents.map((hid) => (
                      <span
                        key={hid}
                        className="tag-item"
                        style={{ color: "var(--hindsight)", borderColor: "var(--hindsight-border)" }}
                      >
                        {hid}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 5. Recommended Investigation Steps */}
      <div className="content-section">
        <div className="section-heading">
          <Search size={16} color="var(--accent-light)" />
          <span>Recommended Non-Destructive Diagnostic Steps</span>
        </div>

        <div>
          {investigation_steps.map((step) => (
            <div key={step.step_number} className="step-item">
              <div className="step-number">{step.step_number}</div>
              <div className="step-body">
                <div className="step-action">{step.action}</div>
                <div className="step-rationale">{step.rationale}</div>
                <div className="step-target">Target: {step.target_system}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. Remediation Recommendations */}
      <div className="content-section">
        <div className="section-heading">
          <Wrench size={16} color="var(--accent-light)" />
          <span>Remediation Recommendations</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          {/* Immediate Mitigation */}
          <div
            style={{
              background: "#090d16",
              border: "1px solid rgba(249, 115, 22, 0.3)",
              borderRadius: "var(--radius-md)",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                color: "var(--high)",
                fontWeight: 600,
                fontSize: "13px",
                marginBottom: "10px",
                textTransform: "uppercase",
              }}
            >
              <AlertTriangle size={15} />
              <span>Immediate Mitigation (Stop Impact)</span>
            </div>
            <ul style={{ paddingLeft: "18px", fontSize: "13px", color: "#e2e8f0", display: "flex", flexDirection: "column", gap: "8px" }}>
              {remediation_recommendations.immediate_mitigation.map((m, idx) => (
                <li key={idx}>{m}</li>
              ))}
            </ul>
          </div>

          {/* Long-Term Architectural Fixes */}
          <div
            style={{
              background: "#090d16",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              borderRadius: "var(--radius-md)",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                color: "#10b981",
                fontWeight: 600,
                fontSize: "13px",
                marginBottom: "10px",
                textTransform: "uppercase",
              }}
            >
              <CheckCircle2 size={15} />
              <span>Long-Term Fixes (Prevent Recurrence)</span>
            </div>
            <ul style={{ paddingLeft: "18px", fontSize: "13px", color: "#e2e8f0", display: "flex", flexDirection: "column", gap: "8px" }}>
              {remediation_recommendations.long_term_fix.map((f, idx) => (
                <li key={idx}>{f}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* 7. Limitations & Caveats */}
      {limitations.length > 0 && (
        <div
          style={{
            background: "rgba(255, 255, 255, 0.02)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            padding: "12px 16px",
            fontSize: "12px",
            color: "var(--text-muted)",
          }}
        >
          <strong style={{ color: "var(--text-secondary)" }}>Investigation Caveats: </strong>
          {limitations.join(" • ")}
        </div>
      )}
    </div>
  );
};
