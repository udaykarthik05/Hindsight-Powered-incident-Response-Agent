export interface HindsightConnectionStatus {
  connected: boolean;
  base_url: string;
  bank_id: string;
  server_version?: string | null;
  error?: string | null;
  message: string;
}

export interface BackendHealth {
  status: string;
  app: string;
  environment: string;
  timestamp: string;
}
