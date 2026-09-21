import { Button } from "@/components/atoms/Button";

interface SessionCardProps {
  username: string;
  onSignOut: () => void;
  isSigningOut: boolean;
}

export function SessionCard({ username, onSignOut, isSigningOut }: SessionCardProps) {
  return (
    <div className="flex flex-col gap-2 px-1">
      <p className="truncate text-xs text-muted">Signed in as {username}</p>
      <Button variant="ghost" onClick={onSignOut} disabled={isSigningOut} className="w-full text-left">
        {isSigningOut ? "Signing out..." : "Sign out"}
      </Button>
    </div>
  );
}
