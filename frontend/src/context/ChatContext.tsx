import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import axios from "axios";
import { useQueryClient } from "@tanstack/react-query";
import { chatApi, extractErrorMessage } from "../lib/api";
import {
  type ChatMessage,
  type ChatReply,
  type ConfirmResult,
  type PendingState,
} from "../lib/chatTypes";

interface ChatContextValue {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  messages: ChatMessage[];
  isSending: boolean;
  send: (text: string) => Promise<void>;
  confirm: (messageId: string) => Promise<void>;
  cancelAction: (messageId: string) => void;
  reset: () => void;
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

let nextId = 0;
const newId = () => `m${Date.now()}-${nextId++}`;

function describeSendError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 429) return "You are sending messages too quickly. Wait a moment and try again.";
    if (error.response?.status === 403) return "Your role is not allowed to use the assistant.";
    if (!error.response) return "Could not reach the assistant service. Check your connection and try again.";
  }
  return extractErrorMessage(error);
}

// State lives here, not in the panel: every page renders its own AppShell, so a panel-local
// conversation would be wiped on each navigation.
export function ChatProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const conversationId = useRef<string | null>(null);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "j") {
        e.preventDefault();
        setIsOpen((v) => !v);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setMessages((prev) => [...prev, { id: newId(), role: "user", text: trimmed, toolCalls: [] }]);
    setIsSending(true);
    try {
      const res = await chatApi.post<ChatReply>("/chat", {
        message: trimmed,
        conversation_id: conversationId.current,
      });
      conversationId.current = res.data.conversation_id;
      const pending: PendingState | undefined = res.data.pending_action
        ? { action: res.data.pending_action, status: "awaiting" }
        : undefined;
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", text: res.data.reply, toolCalls: res.data.tool_calls, pending },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", text: describeSendError(error), toolCalls: [], isError: true },
      ]);
    } finally {
      setIsSending(false);
    }
  }, []);

  const updatePending = useCallback((messageId: string, update: Partial<PendingState>) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === messageId && m.pending ? { ...m, pending: { ...m.pending, ...update } } : m))
    );
  }, []);

  const confirm = useCallback(
    async (messageId: string) => {
      const target = messages.find((m) => m.id === messageId);
      if (!target?.pending || target.pending.status !== "awaiting") return;
      updatePending(messageId, { status: "confirming" });
      try {
        const res = await chatApi.post<ConfirmResult>("/chat/confirm", { token: target.pending.action.token });
        const ok = res.data.status === "success";
        updatePending(messageId, { status: ok ? "confirmed" : "failed", message: res.data.message });
        // The action changed real data; refresh whatever page is open behind the panel.
        if (ok) await queryClient.invalidateQueries();
      } catch (error) {
        updatePending(messageId, { status: "failed", message: extractErrorMessage(error) });
      }
    },
    [messages, queryClient, updatePending]
  );

  const cancelAction = useCallback(
    (messageId: string) => updatePending(messageId, { status: "cancelled", message: "Cancelled. Nothing was changed." }),
    [updatePending]
  );

  const reset = useCallback(() => {
    conversationId.current = null;
    setMessages([]);
  }, []);

  const value = useMemo(
    () => ({ isOpen, open, close, messages, isSending, send, confirm, cancelAction, reset }),
    [isOpen, open, close, messages, isSending, send, confirm, cancelAction, reset]
  );
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
