import React from "react";
import { Activity, Database, Plus, RefreshCw, ShieldAlert } from "lucide-react";
import { HindsightConnectionStatus } from "../types";

interface Props {
  backendConnected: boolean;
  hindsightStatus: HindsightConnectionStatus | null;
  onRefresh: () => void;
  onOpenCreateModal: () => void;
  refreshing: boolean;
}

export const Header: React.FC<Props> = ({
  backendConnected,
  hindsightStatus,
  onRefresh,
  onOpenCreateModal,
  refreshing,
}) => {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">
          <ShieldAlert size={20} />
        </div>
        <div>
          <div className="brand-title">
            Incident Response Agent
            <span className="brand-tag">Hindsight SRE</span>
          </div>
        </div>
      </div>

      <div className="header-status-group">
        {/* Backend Server Status */}
        <div
          className="status-pill"
          title={backendConnected ? "FastAPI backend running" : "FastAPI backend unreachable"}
        >
          <span
            className={`status-indicator-dot ${backendConnected ? "dot-green" : "dot-red"}`}
          />
          <Activity size={13} />
          <span>API: {backendConnected ? "Online" : "Offline"}</span>
        </div>

        {/* Hindsight Memory Status */}
        <div
          className="status-pill"
          title={
            hindsightStatus?.connected
              ? `Hindsight Memory v${hindsightStatus.server_version} connected`
              : "Hindsight service unreachable - will gracefully skip historical lookup"
          }
        >
          <span
            className={`status-indicator-dot ${
              hindsightStatus?.connected ? "dot-green" : "dot-red"
            }`}
          />
          <Database size={13} />
          <span>
            Hindsight: {hindsightStatus?.connected ? "Online" : "Offline"}
          </span>
        </div>

        {/* Refresh Button */}
        <button
          className="btn btn-outline"
          onClick={onRefresh}
          disabled={refreshing}
          title="Refresh incidents and health status"
        >
          <RefreshCw size={14} className={refreshing ? "spinner" : ""} />
          <span>Refresh</span>
        </button>

        {/* Create Incident Button */}
        <button className="btn btn-primary" onClick={onOpenCreateModal}>
          <Plus size={15} />
          <span>Report Incident</span>
        </button>
      </div>
    </header>
  );
};
