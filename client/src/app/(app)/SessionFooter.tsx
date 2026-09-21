"use client";

import { SessionCard } from "@/components/molecules/SessionCard";
import { useLogout } from "@/hooks/useLogout";

export function SessionFooter({ username }: { username: string }) {
  const { isSigningOut, signOut } = useLogout();

  return <SessionCard username={username} onSignOut={signOut} isSigningOut={isSigningOut} />;
}
