"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { getCurrentStaff } from "@/lib/api";
import { clearAccessToken, getAccessToken } from "@/lib/auth-storage";
import type { StaffUser } from "@/types";

export function useStaffAuth() {
  const router = useRouter();
  const [user, setUser] = useState<StaffUser>();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let active = true;
    if (!getAccessToken()) {
      setChecking(false);
      router.replace("/login");
      return () => {
        active = false;
      };
    }
    getCurrentStaff()
      .then((nextUser) => {
        if (active) setUser(nextUser);
      })
      .catch(() => {
        clearAccessToken();
        if (active) router.replace("/login");
      })
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
    };
  }, [router]);

  const logout = useCallback(() => {
    clearAccessToken();
    setUser(undefined);
    router.replace("/login");
  }, [router]);

  return { user, checking, logout };
}
