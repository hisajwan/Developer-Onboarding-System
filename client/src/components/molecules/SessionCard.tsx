import Link from "next/link";
import { Button } from "@/components/atoms/Button";

interface SessionCardProps {
  username: string;
  onSignOut: () => void;
  isSigningOut: boolean;
}

export function SessionCard({ username, onSignOut, isSigningOut }: SessionCardProps) {
  return (
    // px-4 on every line (rather than shrinking the button's own padding, which `cn()` can't
    // reliably override - it's a plain class-string join, not a Tailwind-aware merge) keeps all
    // three lines flush at the same left edge.
    <div className="flex flex-col gap-2">
      <p className="truncate px-4 text-xs text-muted">Signed in as {username}</p>
      <Link href="/account" className="px-4 text-xs font-medium text-primary hover:underline">
        Account settings
      </Link>
      <Button
        variant="ghost"
        onClick={onSignOut}
        disabled={isSigningOut}
        className="w-full text-left"
      >
        {isSigningOut ? "Signing out..." : "Sign out"}
      </Button>
    </div>
  );
}
