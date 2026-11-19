export interface ToolCallInfo {
  name: string;
  label: string;
  status: "ok" | "error" | "pending";
  error: string | null;
}

export interface PendingAction {
  token: string;
  tool: string;
  summary: string;
  details: Record<string, string>;
  expires_at: string;
}

export interface ChatReply {
  reply: string;
  tool_calls: ToolCallInfo[];
  pending_action: PendingAction | null;
  conversation_id: string;
}

export interface ConfirmResult {
  status: "success" | "error";
  http_status: number;
  message: string;
  result: Record<string, unknown> | null;
  already_confirmed: boolean;
}

export type PendingStatus = "awaiting" | "confirming" | "confirmed" | "failed" | "cancelled";

export interface PendingState {
  action: PendingAction;
  status: PendingStatus;
  // Verbatim message from the business API (or the confirm endpoint) once resolved.
  message?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  toolCalls: ToolCallInfo[];
  isError?: boolean;
  pending?: PendingState;
}
