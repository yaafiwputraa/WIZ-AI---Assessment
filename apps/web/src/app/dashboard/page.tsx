"use client";

import { ArrowUpRight, Bot, Clock3, Headphones, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { StaffAccessLoading } from "@/components/staff-access-loading";
import { PriorityBadge, StatusBadge, SummaryBadge } from "@/components/status-badge";
import { useLocale } from "@/hooks/use-locale";
import { useStaffAuth } from "@/hooks/use-staff-auth";
import { getDashboardStats, getEscalations } from "@/lib/api";
import { formatDate, t } from "@/lib/i18n";
import type {
  DashboardStats,
  EscalationListItem,
  EscalationStatus,
  Priority,
} from "@/types";

const emptyStats: DashboardStats = { active_ai: 0, ai_resolved: 0, escalated: 0 };
const priorityRank: Record<Priority, number> = { high: 3, medium: 2, low: 1 };

export default function DashboardPage() {
  const { locale, setLocale } = useLocale();
  const { user, checking, logout } = useStaffAuth();
  const text = t(locale);
  const [stats, setStats] = useState(emptyStats);
  const [tickets, setTickets] = useState<EscalationListItem[]>([]);
  const [status, setStatus] = useState<EscalationStatus | "all">("all");
  const [priority, setPriority] = useState<Priority | "all">("all");
  const [sort, setSort] = useState<"newest" | "priority">("newest");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    if (!user) return;
    try {
      const [nextStats, nextTickets] = await Promise.all([
        getDashboardStats(),
        getEscalations({ status, priority }),
      ]);
      setStats(nextStats);
      setTickets(nextTickets);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [priority, status, user]);

  useEffect(() => {
    if (!user) return;
    load();
    const interval = window.setInterval(load, 3000);
    return () => window.clearInterval(interval);
  }, [load, user]);

  const sorted = useMemo(
    () =>
      [...tickets].sort((a, b) =>
        sort === "priority"
          ? priorityRank[b.priority] - priorityRank[a.priority]
          : new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [sort, tickets],
  );

  const cards = [
    { label: text.statsActive, value: stats.active_ai, icon: Bot, tone: "bg-sky-50 text-sky-700" },
    { label: text.statsResolved, value: stats.ai_resolved, icon: RefreshCw, tone: "bg-mist text-emerald" },
    { label: text.statsEscalated, value: stats.escalated, icon: Headphones, tone: "bg-amber-50 text-amber-700" },
  ];

  if (checking || !user) return <StaffAccessLoading message={text.checkingAccess} />;

  return (
    <main className="min-h-screen bg-[#f6f8f6] pb-16">
      <AppHeader
        locale={locale}
        onLocaleChange={setLocale}
        chatLabel={text.chat}
        dashboardLabel={text.dashboard}
        staffUser={user}
        onLogout={logout}
      />
      <section className="mx-auto w-full max-w-7xl px-5 pt-6 md:px-8 md:pt-10">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <p className="mb-2 text-xs font-black uppercase tracking-[0.2em] text-emerald">TokoMate operations</p>
            <h1 className="text-3xl font-black tracking-[-0.035em] text-ink sm:text-4xl">{text.dashboardTitle}</h1>
            <p className="mt-3 max-w-2xl text-sage">{text.dashboardSub}</p>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold text-sage">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald" /> Live · 3s
          </div>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {cards.map(({ label, value, icon: Icon, tone }) => (
            <article key={label} className="dashboard-card flex items-center gap-4">
              <span className={`grid h-12 w-12 place-items-center rounded-2xl ${tone}`}><Icon size={22} /></span>
              <div><p className="text-3xl font-black tracking-tight text-ink">{value}</p><p className="text-sm font-medium text-sage">{label}</p></div>
            </article>
          ))}
        </div>

        <section className="mt-6 overflow-hidden rounded-[1.75rem] border border-black/5 bg-white shadow-panel">
          <div className="flex flex-col justify-between gap-4 border-b border-black/5 px-5 py-5 md:flex-row md:items-center md:px-6">
            <div><h2 className="text-lg font-black text-ink">{text.statsEscalated}</h2><p className="mt-1 text-xs text-sage">{tickets.length} tickets</p></div>
            <div className="flex flex-wrap gap-2">
              <label className="filter-field">{text.status}
                <select value={status} onChange={(event) => setStatus(event.target.value as EscalationStatus | "all")}>
                  <option value="all">{text.all}</option><option value="open">Open</option><option value="taken_over">Taken over</option>
                </select>
              </label>
              <label className="filter-field">{text.priority}
                <select value={priority} onChange={(event) => setPriority(event.target.value as Priority | "all")}>
                  <option value="all">{text.all}</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
                </select>
              </label>
              <button type="button" onClick={() => setSort(sort === "newest" ? "priority" : "newest")} className="filter-button">
                {sort === "newest" ? <Clock3 size={14} /> : <Headphones size={14} />} {sort}
              </button>
            </div>
          </div>

          {error && <div className="m-5 rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-700">{text.loadError}</div>}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] text-left">
              <thead><tr className="border-b border-black/5 bg-[#fbfcfb] text-[11px] font-black uppercase tracking-[0.14em] text-sage">
                <th className="px-6 py-4">{text.customer}</th><th className="px-4 py-4">{text.issue}</th><th className="px-4 py-4">{text.priority}</th><th className="px-4 py-4">{text.status}</th><th className="px-4 py-4">{text.time}</th><th className="px-6 py-4" />
              </tr></thead>
              <tbody className="divide-y divide-black/5">
                {loading && [0, 1, 2].map((item) => <tr key={item}>{[0, 1, 2, 3, 4, 5].map((cell) => <td key={cell} className="px-5 py-5"><div className="h-4 animate-pulse rounded bg-slate-100" /></td>)}</tr>)}
                {!loading && sorted.map((ticket) => (
                  <tr key={ticket.id} className="group transition hover:bg-mist/40">
                    <td className="px-6 py-5"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-full bg-ink text-xs font-black text-white">{ticket.customer_name.slice(0, 2).toUpperCase()}</span><div><p className="font-bold text-ink">{ticket.customer_name}</p><p className="text-xs text-sage">{ticket.order_id ?? ticket.conversation_id.slice(0, 8)}</p></div></div></td>
                    <td className="px-4 py-5"><div className="flex items-center gap-2"><p className="max-w-[220px] truncate text-sm font-semibold capitalize text-ink">{ticket.issue_category.replaceAll("_", " ")}</p><SummaryBadge status={ticket.summary_status} /></div><p className="mt-1 max-w-[240px] truncate text-xs text-sage">{ticket.reason}</p></td>
                    <td className="px-4 py-5"><PriorityBadge priority={ticket.priority} /></td>
                    <td className="px-4 py-5"><StatusBadge status={ticket.status} /></td>
                    <td className="px-4 py-5 text-sm text-sage">{formatDate(ticket.created_at, locale)}</td>
                    <td className="px-6 py-5 text-right"><Link href={`/dashboard/conversation/${ticket.id}`} className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-black/10 text-sage transition group-hover:border-emerald group-hover:bg-emerald group-hover:text-white" aria-label={text.open}><ArrowUpRight size={16} /></Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!loading && sorted.length === 0 && <div className="grid place-items-center px-6 py-20 text-center"><span className="mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-mist text-emerald"><CheckCircleIcon /></span><p className="font-bold text-ink">{text.noTickets}</p></div>}
        </section>
      </section>
    </main>
  );
}

function CheckCircleIcon() {
  return <span className="text-2xl">✓</span>;
}
