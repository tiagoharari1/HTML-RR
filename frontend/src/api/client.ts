import axios from "axios";

export const http = axios.create({
  baseURL: "/api",
});

// Types
export interface UploadBase2026Response {
  ok: boolean;
  rows: number;
  meses: number[];
  errors: string[];
}

export interface UploadContableResponse {
  ok: boolean;
  rows: number;
  errors: string[];
}

export interface ConfigPayload {
  session_id: string;
  mes_pivot: number;
  horizonte: number;
  dia_corte?: number | null;
  escenario?: string | null;
}

export interface Totales {
  net_revenue: number;
  npv: number;
  bimo: number;
  revenue_margin: number;
}

export interface BuildResult {
  ok: boolean;
  pnl: Record<string, unknown>[];
  info_calibracion: string[];
  warnings_continuidad: string[];
  totales: Totales;
}

export interface StatusResponse {
  precargados: {
    macro: boolean;
    est_orders: boolean;
    est_asp: boolean;
    base_2025: boolean;
  };
}

// API functions
export async function uploadBase2026(
  sessionId: string,
  file: File
): Promise<UploadBase2026Response> {
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("file", file);
  const { data } = await http.post<UploadBase2026Response>("/upload/base2026", form);
  return data;
}

export async function uploadContable(
  sessionId: string,
  file: File
): Promise<UploadContableResponse> {
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("file", file);
  const { data } = await http.post<UploadContableResponse>("/upload/contable", form);
  return data;
}

export async function setConfig(payload: ConfigPayload): Promise<{ ok: boolean }> {
  const { data } = await http.post<{ ok: boolean }>("/config", payload);
  return data;
}

export async function buildPnl(sessionId: string): Promise<BuildResult> {
  const { data } = await http.post<BuildResult>("/build", { session_id: sessionId });
  return data;
}

export async function getActuals(): Promise<{ rows: Record<string, unknown>[] }> {
  const { data } = await http.get("/actuals");
  return data;
}

export async function getBudget(): Promise<{ rows: Record<string, unknown>[] }> {
  const { data } = await http.get("/budget");
  return data;
}

export async function getStatus(): Promise<StatusResponse> {
  const { data } = await http.get<StatusResponse>("/status");
  return data;
}

export function exportPnlUrl(sessionId: string): string {
  return `/api/export/pnl?session_id=${sessionId}`;
}

export function exportEvolutionUrl(sessionId: string): string {
  return `/api/export/evolution?session_id=${sessionId}`;
}
