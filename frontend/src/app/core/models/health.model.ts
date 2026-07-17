export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  database: string;
  qdrant: string;
  ollama: string;
}
