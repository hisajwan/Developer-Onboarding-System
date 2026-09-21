"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { logout } from "@/lib/api/auth";

export function useLogout() {
  const router = useRouter();
  const [isSigningOut, setIsSigningOut] = useState(false);

  const signOut = useCallback(async () => {
    setIsSigningOut(true);
    try {
      await logout();
    } finally {
      // Leave even if the call failed: without the cookie the proxy sends the visitor to /login.
      router.replace("/login");
      router.refresh();
    }
  }, [router]);

  return { isSigningOut, signOut };
}
