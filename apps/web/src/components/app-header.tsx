"use client";

import { Bot, Headphones, LogOut, MessagesSquare, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { LanguageToggle } from "@/components/language-toggle";
import type { Locale, StaffUser } from "@/types";

export function AppHeader({
  locale,
  onLocaleChange,
  chatLabel,
  dashboardLabel,
  staffUser,
  onLogout,
}: {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  chatLabel: string;
  dashboardLabel: string;
  staffUser?: StaffUser;
  onLogout?: () => void;
}) {
  const pathname = usePathname();
  return (
    <header className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-5 py-5 md:px-8">
      <Link href="/chat" className="flex items-center gap-3" aria-label="TokoMate AI home">
        <span className="grid h-11 w-11 place-items-center rounded-2xl bg-ink text-lime shadow-lg shadow-emerald/10">
          <Bot size={23} strokeWidth={2.2} />
        </span>
        <span>
          <span className="block text-lg font-black tracking-tight text-ink">TokoMate</span>
          <span className="block text-[10px] font-bold uppercase tracking-[0.22em] text-emerald">AI support</span>
        </span>
      </Link>
      <div className="flex items-center gap-2 md:gap-4">
        <nav className="hidden items-center gap-1 rounded-full border border-black/5 bg-white/70 p-1 shadow-sm sm:flex">
          <Link
            href="/chat"
            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition ${
              pathname === "/chat" ? "bg-mist text-emerald" : "text-sage hover:text-ink"
            }`}
          >
            <MessagesSquare size={15} /> {chatLabel}
          </Link>
          <Link
            href="/dashboard"
            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition ${
              pathname.startsWith("/dashboard") ? "bg-mist text-emerald" : "text-sage hover:text-ink"
            }`}
          >
            <Headphones size={15} /> {dashboardLabel}
          </Link>
        </nav>
        {staffUser && (
          <div className="hidden items-center gap-2 rounded-full border border-black/5 bg-white px-3 py-2 md:flex">
            <ShieldCheck size={15} className="text-emerald" />
            <span className="text-xs font-bold text-ink">{staffUser.full_name}</span>
            <span className="rounded-full bg-mist px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-emerald">
              {staffUser.role}
            </span>
          </div>
        )}
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className="grid h-10 w-10 place-items-center rounded-full border border-black/5 bg-white text-sage transition hover:border-red-200 hover:bg-red-50 hover:text-red-700"
            aria-label="Log out"
          >
            <LogOut size={16} />
          </button>
        )}
        <LanguageToggle locale={locale} onChange={onLocaleChange} />
      </div>
    </header>
  );
}
