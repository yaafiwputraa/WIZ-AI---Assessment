"use client";

import { ArrowLeft, CalendarDays, ClipboardList, Headphones, Package, UserRound } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { PriorityBadge, StatusBadge } from "@/components/status-badge";
import { useLocale } from "@/hooks/use-locale";
import { getEscalation, takeOverEscalation } from "@/lib/api";
import { formatDate, t } from "@/lib/i18n";
import type { Conversation } from "@/types";

export default function ConversationDetailPage() {
  const params = useParams<{ id: string }>();
  const { locale, setLocale } = useLocale();
  const text = t(locale);
  const [conversation, setConversation] = useState<Conversation>();
  const [loading, setLoading] = useState(true);
  const [takingOver, setTakingOver] = useState(false);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setConversation(await getEscalation(params.id));
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    load();
    const interval = window.setInterval(load, 3000);
    return () => window.clearInterval(interval);
  }, [load]);

  const takeover = async () => {
    if (!conversation?.escalation) return;
    setTakingOver(true);
    try {
      await takeOverEscalation(conversation.escalation.id);
      await load();
    } finally {
      setTakingOver(false);
    }
  };

  const escalation = conversation?.escalation;

  return (
    <main className="min-h-screen bg-[#f6f8f6] pb-16">
      <AppHeader locale={locale} onLocaleChange={setLocale} chatLabel={text.chat} dashboardLabel={text.dashboard} />
      <section className="mx-auto w-full max-w-7xl px-5 pt-5 md:px-8 md:pt-9">
        <Link href="/dashboard" className="mb-6 inline-flex items-center gap-2 text-sm font-bold text-sage transition hover:text-emerald"><ArrowLeft size={16} />{text.back}</Link>
        {error && <div className="rounded-2xl bg-red-50 p-4 font-semibold text-red-700">{text.loadError}</div>}
        {loading && <DetailSkeleton />}
        {conversation && escalation && (
          <>
            <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
              <div>
                <div className="mb-3 flex flex-wrap items-center gap-2"><PriorityBadge priority={escalation.priority} /><StatusBadge status={escalation.status} /></div>
                <h1 className="text-3xl font-black tracking-[-0.035em] text-ink sm:text-4xl">{text.caseDetail}</h1>
                <p className="mt-2 font-mono text-xs text-sage">#{escalation.id.slice(0, 12).toUpperCase()}</p>
              </div>
              <button type="button" onClick={takeover} disabled={takingOver || escalation.status === "taken_over"} className="primary-button min-w-44">
                <Headphones size={17} /> {escalation.status === "taken_over" ? text.takenOver : takingOver ? "…" : text.takeover}
              </button>
            </div>

            <div className="mt-8 grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
              <aside className="space-y-5">
                <section className="detail-card">
                  <h2 className="section-title"><UserRound size={17} />{text.customer}</h2>
                  <p className="mt-5 text-xl font-black text-ink">{conversation.customer_name}</p>
                  <div className="mt-5 space-y-4 border-t border-black/5 pt-5 text-sm">
                    <InfoRow icon={Package} label={text.order} value={escalation.order_id ?? "—"} />
                    <InfoRow icon={CalendarDays} label={text.created} value={formatDate(escalation.created_at, locale)} />
                    <InfoRow icon={ClipboardList} label={text.issue} value={escalation.issue_category.replaceAll("_", " ")} />
                  </div>
                </section>
                <section className="detail-card">
                  <h2 className="section-title"><ClipboardList size={17} />{text.reason}</h2>
                  <p className="mt-4 text-sm leading-6 text-sage">{escalation.reason}</p>
                </section>
              </aside>

              <div className="space-y-5">
                <section className="detail-card overflow-hidden">
                  <div className="flex items-center justify-between"><h2 className="section-title"><span className="grid h-7 w-7 place-items-center rounded-lg bg-lime text-xs font-black text-ink">AI</span>{text.aiSummary}</h2><span className="text-xs font-bold uppercase tracking-widest text-sage">{escalation.summary_status}</span></div>
                  {escalation.summary_status === "pending" && <div className="mt-5 space-y-3">{["w-full", "w-5/6", "w-3/4"].map((width) => <div key={width} className={`h-4 animate-pulse rounded bg-slate-100 ${width}`} />)}<p className="pt-2 text-sm text-sage">{text.summaryPending}</p></div>}
                  {escalation.summary_status === "failed" && <p className="mt-5 rounded-2xl bg-red-50 p-4 text-sm font-medium text-red-700">{text.summaryFailed}</p>}
                  {escalation.summary_status === "ready" && <div className="summary-copy mt-5 whitespace-pre-wrap">{escalation.summary}</div>}
                </section>

                <section className="detail-card">
                  <div className="mb-6 flex items-center justify-between"><h2 className="section-title"><Headphones size={17} />{text.transcript}</h2><span className="rounded-full bg-mist px-3 py-1 text-xs font-bold text-emerald">{conversation.messages.length} messages</span></div>
                  <div className="space-y-5">
                    {conversation.messages.map((message) => (
                      <div key={message.id} className="flex gap-3">
                        <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-black ${message.sender === "customer" ? "bg-ink text-white" : "bg-mist text-emerald"}`}>{message.sender === "customer" ? conversation.customer_name.slice(0, 1).toUpperCase() : "AI"}</span>
                        <div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-3"><p className="text-sm font-bold capitalize text-ink">{message.sender === "customer" ? conversation.customer_name : "TokoMate AI"}</p><time className="text-[11px] text-sage">{formatDate(message.created_at, locale)}</time></div><p className="mt-1.5 whitespace-pre-wrap text-sm leading-6 text-sage">{message.content}</p></div>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </div>
          </>
        )}
      </section>
    </main>
  );
}

function InfoRow({ icon: Icon, label, value }: { icon: typeof Package; label: string; value: string }) {
  return <div className="flex items-start gap-3"><Icon size={16} className="mt-0.5 text-emerald" /><div><p className="text-xs font-semibold text-sage">{label}</p><p className="mt-0.5 font-bold capitalize text-ink">{value}</p></div></div>;
}

function DetailSkeleton() {
  return <div className="mt-8 grid gap-6 lg:grid-cols-3">{[0, 1, 2].map((item) => <div key={item} className="h-64 animate-pulse rounded-[1.75rem] bg-white shadow-sm" />)}</div>;
}

