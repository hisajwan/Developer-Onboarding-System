import Link from "next/link";
import { cn } from "@/lib/cn";

interface NavItemProps {
  href: string;
  label: string;
  active: boolean;
}

export function NavItem({ href, label, active }: NavItemProps) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "block rounded-lg px-4 py-2 text-sm",
        active ? "bg-primary-soft font-bold text-primary" : "text-muted hover:text-ink",
      )}
    >
      {label}
    </Link>
  );
}
