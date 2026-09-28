import React from "react";
import { IncidentStatus } from "../types";

interface Props {
  status: IncidentStatus;
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  const norm = (status || "open").toLowerCase();
  return <span className={`badge badge-${norm}`}>{norm}</span>;
};
