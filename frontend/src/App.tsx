import React, { useCallback, useEffect, useState } from "react";
import { WifiOff } from "lucide-react";
import { api } from "./api/client";
import { CreateIncidentModal } from "./components/CreateIncidentModal";
import { Header } from "./components/Header";
import { IncidentDetail } from "./components/IncidentDetail";
import { IncidentList } from "./components/IncidentList";
import {
  HindsightConnectionStatus,
  Incident,
  IncidentCreate,
  IncidentResolve,
  InvestigationResult,
} from "./types";

export const App: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [investigationResults, setInvestigationResults] = useState<Record<string, InvestigationResult>>({});

  const [backendConnected, setBackendConnected] = useState<boolean>(true);
  const [hindsightStatus, setHindsightStatus] = useState<HindsightConnectionStatus | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [investigating, setInvestigating] = useState<boolean>(false);
  const [investigationError, setInvestigationError] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  // Check health and load incidents
  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    else setRefreshing(true);
    setBackendError(null);

    try {
      // 1. Check Backend Health
      const health = await api.getHealth();
      setBackendConnected(health.status === "ok");

      // 2. Check Hindsight Status
      try {
        const hsStatus = await api.getHindsightStatus();
        setHindsightStatus(hsStatus);
      } catch {
        setHindsightStatus(null);
      }

      // 3. Fetch Incidents
      const list = await api.getIncidents();
      setIncidents(list);

      // Auto-select first incident if none selected
      if (list.length > 0 && !selectedIncidentId) {
        setSelectedIncidentId(list[0].incident_id);
      }
    } catch (err: any) {
      setBackendConnected(false);
      setBackendError(err.message || "Failed to connect to backend server.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedIncidentId]);

  useEffect(() => {
    loadData(true);
  }, []);

  const selectedIncident = incidents.find((i) => i.incident_id === selectedIncidentId) || null;
  const currentInvestigationResult = selectedIncidentId
    ? investigationResults[selectedIncidentId] || null
    : null;

  // Run AI investigation on the selected incident
  const handleInvestigate = async (id: string) => {
    setInvestigating(true);
    setInvestigationError(null);

    try {
      const result = await api.investigateIncident(id);
      setInvestigationResults((prev) => ({
        ...prev,
        [id]: result,
      }));
    } catch (err: any) {
      setInvestigationError(err.message || "Investigation failed.");
    } finally {
      setInvestigating(false);
    }
  };

  // Create new incident
  const handleCreateIncident = async (payload: IncidentCreate) => {
    const created = await api.createIncident(payload);
    setIncidents((prev) => [created, ...prev]);
    setSelectedIncidentId(created.incident_id);
  };

  // Resolve incident
  const handleResolveIncident = async (id: string, payload: IncidentResolve) => {
    const resolved = await api.resolveIncident(id, payload);
    setIncidents((prev) =>
      prev.map((inc) => (inc.incident_id === id ? resolved : inc))
    );
    return resolved;
  };

  return (
    <div className="app-container">
      {/* Header */}
      <Header
        backendConnected={backendConnected}
        hindsightStatus={hindsightStatus}
        onRefresh={() => loadData(false)}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
        refreshing={refreshing}
      />

      {/* Backend Offline Banner */}
      {!backendConnected && (
        <div
          style={{
            background: "rgba(244, 63, 94, 0.15)",
            borderBottom: "1px solid rgba(244, 63, 94, 0.4)",
            color: "#fecdd3",
            padding: "10px 24px",
            fontSize: "13px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <WifiOff size={16} color="#f43f5e" />
            <span>
              <strong>Backend Disconnected:</strong> {backendError}
            </span>
          </div>
          <button
            className="btn btn-outline"
            style={{ padding: "3px 10px", fontSize: "11px" }}
            onClick={() => loadData(false)}
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Main Workspace Split View */}
      <div className="main-content">
        <IncidentList
          incidents={incidents}
          selectedId={selectedIncidentId}
          onSelect={(id) => {
            setSelectedIncidentId(id);
            setInvestigationError(null);
          }}
          loading={loading}
        />

        <IncidentDetail
          incident={selectedIncident}
          investigationResult={currentInvestigationResult}
          onInvestigate={handleInvestigate}
          onResolve={handleResolveIncident}
          investigating={investigating}
          investigationError={investigationError}
        />
      </div>

      {/* Create Modal */}
      <CreateIncidentModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateIncident}
      />
    </div>
  );
};
