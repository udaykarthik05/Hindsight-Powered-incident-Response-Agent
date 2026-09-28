import React from "react";
import { Severity } from "../types";

interface Props {
  severity: Severity;
}

export const SeverityBadge: React.FC<Props> = ({ severity }) => {
  const norm = (severity || "medium").toLowerCase();
  return <span className={`badge badge-${norm}`}>{norm}</span>;
};
