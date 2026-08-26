import type {
  ChatResponse,
  Conversation,
  DashboardStats,
  Escalation,
  EscalationListItem,
  EscalationStatus,
  Locale,
  Priority,
  StaffLoginResponse,
  StaffUser,
} from "@/types";
import { clearAccessToken, getAccessToken } from "@/lib/auth-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public retryable = false,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) clearAccessToken();
    const detail = payload?.error;
    throw new ApiError(
      detail?.code ?? "request_failed",
      detail?.message ?? "The request could not be completed.",
      detail?.retryable ?? response.status >= 500,
    );
  }
  return payload as T;
}

export function loginStaff(email: string, password: string) {
  return request<StaffLoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function getCurrentStaff() {
  return request<StaffUser>("/api/auth/me");
}

export function sendChat(input: {
  conversation_id?: string;
  customer_name?: string;
  locale: Locale;
  message: string;
}) {
  return request<ChatResponse>("/api/chat", { method: "POST", body: JSON.stringify(input) });
}

export function getConversation(id: string) {
  return request<Conversation>(`/api/conversations/${id}`);
}

export function resolveConversation(id: string) {
  return request<Conversation>(`/api/conversations/${id}/resolve`, { method: "POST" });
}

export function getDashboardStats() {
  return request<DashboardStats>("/api/dashboard/stats");
}

export function getEscalations(filters: {
  status?: EscalationStatus | "all";
  priority?: Priority | "all";
}) {
  const params = new URLSearchParams();
  if (filters.status && filters.status !== "all") params.set("status", filters.status);
  if (filters.priority && filters.priority !== "all") params.set("priority", filters.priority);
  return request<EscalationListItem[]>(`/api/escalations?${params.toString()}`);
}

export function getEscalation(id: string) {
  return request<Conversation>(`/api/escalations/${id}`);
}

export function takeOverEscalation(id: string) {
  return request<Escalation>(`/api/escalations/${id}/takeover`, { method: "POST" });
}
