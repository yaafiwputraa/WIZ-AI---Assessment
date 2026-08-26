export type Locale = "id" | "en";
export type ConversationStatus = "ai_active" | "escalated" | "human_active" | "resolved";
export type Priority = "low" | "medium" | "high";
export type EscalationStatus = "open" | "taken_over";
export type SummaryStatus = "pending" | "ready" | "failed";
export type Sender = "customer" | "assistant" | "agent" | "system";
export type StaffRole = "agent" | "admin";

export interface StaffUser {
  id: string;
  email: string;
  full_name: string;
  role: StaffRole;
}

export interface StaffLoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: StaffUser;
}

export interface Message {
  id: string;
  sender: Sender;
  content: string;
  tool_metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface Escalation {
  id: string;
  conversation_id: string;
  order_id: string | null;
  issue_category: string;
  reason: string;
  priority: Priority;
  status: EscalationStatus;
  summary: string | null;
  summary_status: SummaryStatus;
  created_at: string;
  taken_over_at: string | null;
}

export interface Conversation {
  id: string;
  customer_name: string;
  locale: Locale;
  status: ConversationStatus;
  detected_order_id: string | null;
  created_at: string;
  updated_at: string;
  messages: Message[];
  escalation: Escalation | null;
}

export interface ChatResponse {
  conversation_id: string;
  conversation_status: ConversationStatus;
  user_message: Message;
  assistant_message: Message;
  tool_trace_identifiers: string[];
  escalation: Escalation | null;
}

export interface DashboardStats {
  active_ai: number;
  ai_resolved: number;
  escalated: number;
}

export interface EscalationListItem {
  id: string;
  conversation_id: string;
  customer_name: string;
  order_id: string | null;
  issue_category: string;
  reason: string;
  priority: Priority;
  status: EscalationStatus;
  summary_status: SummaryStatus;
  created_at: string;
}
