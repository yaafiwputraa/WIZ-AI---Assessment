"use client";

import { ArrowRight, LockKeyhole, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { useLocale } from "@/hooks/use-locale";
import { getCurrentStaff, loginStaff } from "@/lib/api";
import { getAccessToken, storeAccessToken } from "@/lib/auth-storage";
import { t } from "@/lib/i18n";

const DEMO_EMAIL = "agent@tokomate.local";
const DEMO_PASSWORD = "DemoAgent123!";

export default function LoginPage() {
  const router = useRouter();
  const { locale, setLocale } = useLocale();
  const text = t(locale);
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    if (!getAccessToken()) return;
    getCurrentStaff()
      .then(() => router.replace("/dashboard"))
      .catch(() => undefined);
  }, [router]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(undefined);
    try {
      const response = await loginStaff(email, password);
      storeAccessToken(response.access_token);
      router.replace("/dashboard");
    } catch {
      setError(text.invalidLogin);
    } finally {
      setLoading(false);
    }
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
      <section className="relative mx-auto grid min-h-[calc(100vh-100px)] w-full max-w-7xl place-items-center px-5 pb-16 md:px-8">
        <div className="w-full max-w-md rounded-[2rem] border border-black/5 bg-white p-6 shadow-panel sm:p-8">
          <div className="mb-6 flex items-start gap-4">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-mist text-emerald">
              <LockKeyhole size={22} />
            </span>
            <div>
              <div className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.16em] text-emerald">
                <ShieldCheck size={13} /> {text.protectedDashboard}
              </div>
              <h1 className="text-2xl font-black tracking-tight text-ink">{text.loginTitle}</h1>
              <p className="mt-2 text-sm leading-6 text-sage">{text.loginSub}</p>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <label className="block text-sm font-bold text-ink" htmlFor="staff-email">
              {text.email}
              <input
                id="staff-email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="field mt-2"
                required
              />
            </label>
            <label className="block text-sm font-bold text-ink" htmlFor="staff-password">
              {text.password}
              <input
                id="staff-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="field mt-2"
                minLength={8}
                required
              />
            </label>
            {error && (
              <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
                {error}
              </div>
            )}
            <button type="submit" disabled={loading} className="primary-button w-full">
              {loading ? text.loggingIn : text.login} <ArrowRight size={17} />
            </button>
          </form>

          <div className="mt-6 rounded-2xl border border-emerald/10 bg-mist/60 p-4 text-xs leading-5 text-sage">
            <p className="font-black uppercase tracking-wider text-emerald">{text.demoAccess}</p>
            <p className="mt-2 font-mono">{DEMO_EMAIL}</p>
            <p className="font-mono">{DEMO_PASSWORD}</p>
          </div>
        </div>
      </section>
    </main>
  );
}
