"use client";

import {
  ArrowRight,
  Check,
  CheckCircle2,
  PackageCheck,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { useLocale } from "@/hooks/use-locale";
import { ApiError, resolveConversation, sendChat } from "@/lib/api";
import { t } from "@/lib/i18n";
import type { ConversationStatus, Escalation, Message } from "@/types";

export default function ChatPage() {
  const { locale, setLocale } = useLocale();
  const text = t(locale);
  const [customerName, setCustomerName] = useState("");
  const [started, setStarted] = useState(false);
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<ConversationStatus>("ai_active");
  const [escalation, setEscalation] = useState<Escalation | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const start = (event: FormEvent) => {
    event.preventDefault();
    if (customerName.trim()) setStarted(true);
  };

  const send = async (event: FormEvent) => {
    event.preventDefault();
    const content = input.trim();
    if (!content || loading || status !== "ai_active") return;
    setError(undefined);
    setInput("");
    setLoading(true);
    const tempId = `temp-${Date.now()}`;
    const optimistic: Message = {
      id: tempId,
      sender: "customer",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, optimistic]);
    try {
      const response = await sendChat({
        conversation_id: conversationId,
        customer_name: conversationId ? undefined : customerName,
        locale,
        message: content,
      });
      setConversationId(response.conversation_id);
      setStatus(response.conversation_status);
      setEscalation(response.escalation);
      setMessages((current) => [
        ...current.filter((message) => message.id !== tempId),
        response.user_message,
        response.assistant_message,
      ]);
    } catch (caught) {
      setMessages((current) => current.filter((message) => message.id !== tempId));
      setInput(content);
      setError(caught instanceof ApiError ? caught.message : text.loadError);
    } finally {
      setLoading(false);
    }
  };

  const resolve = async () => {
    if (!conversationId) return;
    setLoading(true);
    try {
      const conversation = await resolveConversation(conversationId);
      setStatus(conversation.status);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : text.loadError);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStarted(false);
    setConversationId(undefined);
    setMessages([]);
    setStatus("ai_active");
    setEscalation(null);
    setCustomerName("");
    setInput("");
    setError(undefined);
  };

  return (
    <main className="min-h-screen overflow-hidden bg-sand">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <AppHeader
        locale={locale}
        onLocaleChange={setLocale}
        chatLabel={text.chat}
        dashboardLabel={text.dashboard}
      />

      <section className="relative mx-auto grid w-full max-w-7xl gap-10 px-5 pb-10 pt-4 md:px-8 lg:grid-cols-[0.82fr_1.18fr] lg:items-center lg:pb-16 lg:pt-10">
        <div className="max-w-xl py-4 lg:py-10">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald/15 bg-white/70 px-3 py-2 text-xs font-bold uppercase tracking-[0.15em] text-emerald shadow-sm">
            <Sparkles size={14} /> {text.eyebrow}
          </div>
          <h1 className="text-balance text-4xl font-black leading-[1.05] tracking-[-0.045em] text-ink sm:text-5xl lg:text-6xl">
            {text.headline}
          </h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-sage sm:text-lg">{text.subhead}</p>
          <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            <div className="feature-pill"><PackageCheck size={18} /> Real-time business data</div>
            <div className="feature-pill"><ShieldCheck size={18} /> Safe human handoff</div>
          </div>
        </div>

        <div className="chat-shell">
          <div className="flex items-center justify-between border-b border-black/5 px-5 py-4 sm:px-6">
            <div className="flex items-center gap-3">
              <span className="relative grid h-10 w-10 place-items-center rounded-2xl bg-emerald text-sm font-black text-white">
                TM<span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white bg-lime" />
              </span>
              <div>
                <p className="font-bold text-ink">TokoMate AI</p>
                <p className="flex items-center gap-1.5 text-xs font-medium text-sage">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald" /> {text.online}
                </p>
              </div>
            </div>
            {conversationId && status === "ai_active" && (
              <button type="button" onClick={resolve} className="ghost-button">
                <Check size={15} /> <span className="hidden sm:inline">{text.resolved}</span>
              </button>
            )}
          </div>

          {!started ? (
            <form onSubmit={start} className="grid min-h-[480px] place-items-center px-6 py-12">
              <div className="w-full max-w-sm text-center">
                <div className="mx-auto mb-6 grid h-20 w-20 place-items-center rounded-[2rem] bg-mist text-emerald">
                  <Sparkles size={34} />
                </div>
                <h2 className="text-2xl font-black tracking-tight text-ink">{text.headline}</h2>
                <p className="mt-2 text-sm leading-6 text-sage">{text.subhead}</p>
                <label className="mt-8 block text-left text-sm font-bold text-ink" htmlFor="customer-name">
                  {text.nameLabel}
                </label>
                <input
                  id="customer-name"
                  value={customerName}
                  onChange={(event) => setCustomerName(event.target.value)}
                  placeholder={text.namePlaceholder}
                  maxLength={120}
                  autoFocus
                  className="field mt-2"
                />
                <button type="submit" disabled={!customerName.trim()} className="primary-button mt-4 w-full">
                  {text.start} <ArrowRight size={17} />
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className="chat-messages">
                {messages.length === 0 && (
                  <div className="my-auto text-center">
                    <div className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-3xl bg-mist text-emerald">
                      <Sparkles size={27} />
                    </div>
                    <p className="font-bold text-ink">{text.headline}</p>
                    <div className="mx-auto mt-5 grid max-w-sm gap-2">
                      {text.quick.map((prompt) => (
                        <button key={prompt} type="button" onClick={() => setInput(prompt)} className="quick-prompt">
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {messages.map((message) => (
                  <div key={message.id} className={`message-row ${message.sender === "customer" ? "justify-end" : "justify-start"}`}>
                    <div className={`message-bubble ${message.sender === "customer" ? "message-user" : "message-ai"}`}>
                      {message.content}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="message-row justify-start">
                    <div className="message-ai message-bubble flex items-center gap-3 text-sage">
                      <span className="typing"><i /><i /><i /></span>{text.thinking}
                    </div>
                  </div>
                )}
                {status === "escalated" && escalation && (
                  <div className="notice-card border-amber-200 bg-amber-50 text-amber-950">
                    <ShieldCheck size={22} />
                    <div><p className="font-bold">{text.escalationTitle}</p><p className="mt-1 text-sm opacity-75">{text.escalationBody}</p></div>
                  </div>
                )}
                {status === "resolved" && (
                  <div className="notice-card border-emerald/20 bg-mist text-ink">
                    <CheckCircle2 size={22} className="text-emerald" />
                    <div><p className="font-bold">{text.resolvedTitle}</p><p className="mt-1 text-sm text-sage">{text.resolvedBody}</p></div>
                  </div>
                )}
                {error && <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}
                <div ref={endRef} />
              </div>
              {status === "ai_active" ? (
                <form onSubmit={send} className="border-t border-black/5 bg-white px-4 py-4 sm:px-5">
                  <div className="flex items-end gap-2 rounded-[1.4rem] border border-black/10 bg-sand p-2 focus-within:border-emerald/50 focus-within:ring-4 focus-within:ring-emerald/5">
                    <textarea
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" && !event.shiftKey) {
                          event.preventDefault();
                          event.currentTarget.form?.requestSubmit();
                        }
                      }}
                      rows={1}
                      maxLength={4000}
                      placeholder={text.inputPlaceholder}
                      className="max-h-28 min-h-10 flex-1 resize-none bg-transparent px-3 py-2 text-sm text-ink outline-none placeholder:text-sage/60"
                    />
                    <button type="submit" disabled={!input.trim() || loading} className="send-button" aria-label={text.send}>
                      <Send size={18} />
                    </button>
                  </div>
                </form>
              ) : (
                <div className="border-t border-black/5 bg-white p-4">
                  <button type="button" onClick={reset} className="primary-button mx-auto">
                    {text.newChat} <ArrowRight size={17} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </main>
  );
}
