"use client";

import { usePathname } from "next/navigation";
import { NavItem } from "@/components/molecules/NavItem";
import type { NavEntry } from "@/config/navigation";

export function SidebarNav({ entries }: { entries: NavEntry[] }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="flex flex-col gap-1">
      {entries.map((entry) => (
        <NavItem key={entry.href} {...entry} active={pathname.startsWith(entry.href)} />
      ))}
    </nav>
  );
}
