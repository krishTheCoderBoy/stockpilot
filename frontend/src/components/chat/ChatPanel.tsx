import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Bot, PackageSearch, Plus, Send, ShoppingCart, TrendingDown, X, type LucideIcon } from "lucide-react";
import { useChat } from "../../context/ChatContext";
import { type ChatMessage, type ToolCallInfo } from "../../lib/chatTypes";
import { ConfirmationCard } from "./ConfirmationCard";

const SUGGESTIONS: { icon: LucideIcon; text: string }[] = [
  { icon: TrendingDown, text: "Which products are likely to stock out soon?" },
  { icon: PackageSearch, text: "Show low-stock items" },
  { icon: ShoppingCart, text: "What should we reorder from our suppliers?" },
];

const CHIP_STYLE: Record<ToolCallInfo["status"], string> = {
  ok: "border-flow/30 bg-flow/10 text-flow",
  pending: "border-accent/40 bg-accent/10 text-accent",
  error: "border-danger/30 bg-danger/10 text-danger",
};

const GREETING_SEEN_KEY = "stockpilot-chat-greeting-seen";

function BotAvatar({ size = "md", online = false }: { size?: "sm" | "md" | "lg"; online?: boolean }) {
  const box = { sm: "h-7 w-7", md: "h-10 w-10", lg: "h-16 w-16" }[size];
  const icon = { sm: 14, md: 20, lg: 32 }[size];
  return (
    <span className={`relative flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-accent to-flow text-ink shadow-md ${box}`}>
      <Bot size={icon} strokeWidth={2.2} />
      {online && (
        <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-surface bg-flow" aria-hidden />
      )}
    </span>
  );
}

function ToolChips({ calls }: { calls: ToolCallInfo[] }) {
  if (calls.length === 0) return null;
  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {calls.map((call, i) => (
        <span
          key={i}
          title={call.error ?? undefined}
          className={`rounded-full border px-2 py-0.5 text-[11px] ${CHIP_STYLE[call.status]}`}
        >
          {call.label}
          {call.status === "error" && " (failed)"}
        </span>
      ))}
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const { confirm, cancelAction } = useChat();

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-sm bg-gradient-to-br from-accent to-accent-muted px-3.5 py-2 text-sm text-ink shadow-sm">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2">
      <BotAvatar size="sm" />
      <div className="min-w-0 flex-1">
        <div
          className={`inline-block max-w-[92%] whitespace-pre-wrap break-words rounded-2xl rounded-tl-sm px-3.5 py-2 text-sm text-text shadow-sm ${
            message.isError ? "border border-danger/30 bg-danger/5" : "border border-border bg-ink/60"
          }`}
        >
          {message.text}
        </div>
        <ToolChips calls={message.toolCalls} />
        {message.pending && (
          <div className="max-w-[95%]">
            <ConfirmationCard
              pending={message.pending}
              onConfirm={() => void confirm(message.id)}
              onCancel={() => cancelAction(message.id)}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function TypingBubble({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <div className="flex items-start gap-2" role="status" aria-live="polite">
      <BotAvatar size="sm" />
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-border bg-ink/60 px-3.5 py-3">
        {reducedMotion ? (
          <span className="text-xs text-text-muted">Thinking...</span>
        ) : (
          [0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-2 w-2 animate-bounce rounded-full bg-accent/80"
              style={{ animationDelay: `${i * 140}ms` }}
              aria-hidden
            />
          ))
        )}
        <span className="sr-only">The assistant is thinking</span>
      </div>
    </div>
  );
}

function Welcome({ onPick, disabled }: { onPick: (text: string) => void; disabled: boolean }) {
  return (
    <div className="flex flex-col items-center px-2 pt-4 text-center">
      <BotAvatar size="lg" online />
      <h3 className="mt-3 text-base font-medium text-text">Hi, I'm your StockPilot assistant</h3>
      <p className="mt-1 max-w-[18rem] text-sm text-text-muted">
        Ask about stock, purchase orders, suppliers or forecasts. I can prepare actions too, but nothing changes until you confirm it.
      </p>
      <div className="mt-4 flex w-full flex-col gap-2">
        {SUGGESTIONS.map(({ icon: Icon, text }) => (
          <button
            key={text}
            onClick={() => onPick(text)}
            disabled={disabled}
            className="flex items-center gap-2.5 rounded-full border border-border bg-ink/60 px-3.5 py-2 text-left text-xs text-text transition-colors hover:border-accent/60 hover:bg-accent/10 disabled:opacity-40"
          >
            <Icon size={14} className="shrink-0 text-accent" />
            {text}
          </button>
        ))}
      </div>
    </div>
  );
}

// Floating assistant: a round bot button fixed to the bottom-right corner that opens a chat
// window over the page. No backdrop, so the page stays usable while it is open.
export function ChatPanel() {
  const { isOpen, open, close, messages, isSending, send, reset } = useChat();
  const reducedMotion = useReducedMotion() ?? false;
  const [draft, setDraft] = useState("");
  const [showGreeting, setShowGreeting] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // A prepared action is waiting for a decision: keep a visible cue on the closed button.
  const hasPendingAction = messages.some((m) => m.pending?.status === "awaiting");

  // A one-time hello above the button, so people notice the assistant exists.
  useEffect(() => {
    let seen = false;
    try {
      seen = sessionStorage.getItem(GREETING_SEEN_KEY) === "1";
    } catch {
      /* storage can be unavailable (private window): just show the greeting */
    }
    if (seen || isOpen) return;
    const timer = setTimeout(() => setShowGreeting(true), 2500);
    return () => clearTimeout(timer);
  }, [isOpen]);

  function dismissGreeting() {
    setShowGreeting(false);
    try {
      sessionStorage.setItem(GREETING_SEEN_KEY, "1");
    } catch {
      /* ignore */
    }
  }

  function openChat() {
    dismissGreeting();
    open();
  }

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") close();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isOpen, close]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "end" });
  }, [messages, isSending, reducedMotion]);

  function submit() {
    const text = draft.trim();
    if (!text || isSending) return;
    setDraft("");
    void send(text);
  }

  const windowMotion = reducedMotion
    ? { initial: { opacity: 1 }, animate: { opacity: 1 }, exit: { opacity: 1 }, transition: { duration: 0 } }
    : {
        initial: { opacity: 0, scale: 0.9, y: 20 },
        animate: { opacity: 1, scale: 1, y: 0 },
        exit: { opacity: 0, scale: 0.9, y: 20 },
        transition: { duration: 0.18, ease: "easeOut" as const },
      };

  return (
    // initial={false}: each page mounts its own AppShell, so without this the window would
    // replay its opening animation on every navigation while it is open.
    <AnimatePresence initial={false}>
      {isOpen ? (
        <motion.section
          key="chat-window"
          {...windowMotion}
          style={{ transformOrigin: "bottom right" }}
          role="dialog"
          aria-label="StockPilot assistant"
          className="fixed bottom-4 right-4 z-40 flex h-[min(660px,calc(100vh-2rem))] w-[min(400px,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl"
        >
          <header className="flex items-center justify-between gap-3 bg-gradient-to-r from-accent/90 to-flow/90 px-4 py-3 text-ink">
            <div className="flex min-w-0 items-center gap-3">
              <span className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-ink/80 text-accent shadow-inner">
                <Bot size={22} strokeWidth={2.2} />
                <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-ink bg-flow" aria-hidden />
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold leading-tight">StockPilot Assistant</p>
                <p className="text-[11px] leading-tight opacity-80">Inventory and procurement helper</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={reset}
                disabled={messages.length === 0}
                aria-label="Start a new chat"
                title="New chat"
                className="rounded-full p-1.5 transition-colors hover:bg-ink/15 disabled:opacity-40"
              >
                <Plus size={16} />
              </button>
              <button
                onClick={close}
                aria-label="Close assistant"
                title="Close (Esc)"
                className="rounded-full p-1.5 transition-colors hover:bg-ink/15"
              >
                <X size={16} />
              </button>
            </div>
          </header>

          <div className="flex-1 space-y-3.5 overflow-y-auto px-4 py-4">
            {messages.length === 0 && <Welcome onPick={(text) => void send(text)} disabled={isSending} />}
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isSending && <TypingBubble reducedMotion={reducedMotion} />}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit();
            }}
            className="border-t border-border bg-surface p-3"
          >
            <div className="flex items-end gap-2 rounded-2xl border border-border bg-ink/60 px-3 py-2 transition-colors focus-within:border-accent">
              <textarea
                ref={inputRef}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submit();
                  }
                }}
                rows={1}
                maxLength={2000}
                placeholder="Ask me anything about your stock..."
                aria-label="Message the assistant"
                className="max-h-28 min-h-[1.5rem] flex-1 resize-none bg-transparent text-sm text-text outline-none placeholder:text-text-muted/60"
              />
              <button
                type="submit"
                disabled={isSending || draft.trim().length === 0}
                aria-label="Send message"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-accent to-flow text-ink shadow transition-opacity hover:opacity-90 disabled:opacity-40"
              >
                <Send size={14} />
              </button>
            </div>
            <p className="mt-1.5 text-center text-[11px] text-text-muted">Enter to send · Shift+Enter for a new line · Ctrl/⌘+J to toggle</p>
          </form>
        </motion.section>
      ) : (
        <motion.div
          key="chat-launcher"
          initial={reducedMotion ? false : { opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={reducedMotion ? { opacity: 0 } : { opacity: 0, scale: 0.8 }}
          transition={{ duration: reducedMotion ? 0 : 0.15 }}
          className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3"
        >
          {showGreeting && (
            <div className="relative max-w-[16rem] rounded-2xl rounded-br-sm border border-border bg-surface px-4 py-3 text-sm text-text shadow-xl">
              <button
                onClick={dismissGreeting}
                aria-label="Dismiss"
                className="absolute -left-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full border border-border bg-surface text-text-muted hover:text-text"
              >
                <X size={11} />
              </button>
              <button onClick={openChat} className="text-left">
                <span className="font-medium">Hi! Need a hand?</span>
                <span className="mt-0.5 block text-xs text-text-muted">Ask me about stock, orders or forecasts.</span>
              </button>
            </div>
          )}

          <motion.button
            whileHover={reducedMotion ? undefined : { scale: 1.08 }}
            whileTap={reducedMotion ? undefined : { scale: 0.94 }}
            onClick={openChat}
            aria-label="Open the StockPilot assistant"
            title="Ask the assistant (Ctrl/⌘+J)"
            className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-accent to-flow text-ink shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 focus-visible:ring-offset-2 focus-visible:ring-offset-ink"
          >
            {/* Soft pulse ring, off for reduced motion. */}
            <span className="absolute inset-0 -z-10 animate-ping rounded-full bg-accent/40 motion-reduce:hidden" aria-hidden />
            <Bot size={30} strokeWidth={2.2} />
            <span className="absolute bottom-0.5 right-0.5 h-3.5 w-3.5 rounded-full border-2 border-ink bg-flow" aria-hidden />
            {hasPendingAction && (
              <span
                className="absolute -right-0.5 -top-0.5 h-4 w-4 rounded-full border-2 border-ink bg-danger"
                title="An action is waiting for your confirmation"
              />
            )}
          </motion.button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
