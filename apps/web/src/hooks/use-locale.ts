"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/types";

export function useLocale() {
  const [locale, setLocaleState] = useState<Locale>("id");

  useEffect(() => {
    const saved = window.localStorage.getItem("tokomate-locale");
    if (saved === "id" || saved === "en") setLocaleState(saved);
  }, []);

  const setLocale = (next: Locale) => {
    setLocaleState(next);
    window.localStorage.setItem("tokomate-locale", next);
  };

  return { locale, setLocale };
}

