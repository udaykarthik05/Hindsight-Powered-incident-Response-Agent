import React, { useMemo, useState } from "react";
import { AlertCircle, Clock, Search } from "lucide-react";
import { Incident } from "../types";
import { SeverityBadge } from "./SeverityBadge";
import { StatusBadge } from "./StatusBadge";

interface Props {
  incidents: Incident[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loading: boolean;
}

export const IncidentList: React.FC<Props> = ({
  incidents,
  selectedId,
  onSelect,
  loading,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      const matchesSearch =
        inc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inc.incident_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inc.affected_service.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus =
        statusFilter === "all" || inc.status === statusFilter;

      const matchesSeverity =
        severityFilter === "all" || inc.severity === severityFilter;

      return matchesSearch && matchesStatus && matchesSeverity;
    });
  }, [incidents, searchTerm, statusFilter, severityFilter]);

  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <aside className="incident-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title-row">
          <span style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>
            Incidents ({filteredIncidents.length})
          </span>
          <div style={{ display: "flex", gap: "6px" }}>
            <select
              className="form-select"
              style={{ padding: "3px 6px", fontSize: "11px" }}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="open">Open</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
            </select>
            <select
              className="form-select"
              style={{ padding: "3px 6px", fontSize: "11px" }}
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <option value="all">All Severity</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div className="search-filter-box">
          <Search size={14} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search by ID, title, service..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Incident List */}
      <div className="incident-card-list">
        {loading ? (
          <div className="empty-state">
            <div className="spinner" style={{ width: 24, height: 24, marginBottom: 12 }} />
            <span>Loading incidents from backend...</span>
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="empty-state">
            <AlertCircle size={28} className="empty-icon" />
            <span style={{ fontWeight: 500, color: "var(--text-secondary)" }}>
              No incidents found
            </span>
            <span style={{ fontSize: "12px", marginTop: 4 }}>
              Try adjusting your search or filter options.
            </span>
          </div>
        ) : (
          filteredIncidents.map((incident) => {
            const isSelected = incident.incident_id === selectedId;
            return (
              <div
                key={incident.incident_id}
                className={`incident-card ${isSelected ? "active" : ""}`}
                onClick={() => onSelect(incident.incident_id)}
              >
                <div className="card-header">
                  <span className="card-id">{incident.incident_id}</span>
                  <div style={{ display: "flex", gap: "6px" }}>
                    <SeverityBadge severity={incident.severity} />
                    <StatusBadge status={incident.status} />
                  </div>
                </div>

                <div className="card-title">{incident.title}</div>

                <div className="card-meta">
                  <span style={{ color: "var(--accent-light)" }}>
                    {incident.affected_service}
                  </span>
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      color: "var(--text-muted)",
                    }}
                  >
                    <Clock size={11} />
                    {formatDate(incident.timestamp)}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
