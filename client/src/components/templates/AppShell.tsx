import type { ReactNode } from "react";
import { APP_NAME } from "@/config/app";

interface AppShellProps {
  sidebar: ReactNode;
  /** Page-specific sidebar content (e.g. the Ask screen's docs upload panel). Sits below the nav. */
  sidebarExtra?: ReactNode;
  sidebarFooter?: ReactNode;
  children: ReactNode;
}

export function AppShell({ sidebar, sidebarExtra, sidebarFooter, children }: AppShellProps) {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 shrink-0 flex-col bg-surface p-4">
        <p className="mb-6 px-1 text-sm font-bold">{APP_NAME}</p>
        {sidebar}
        {sidebarExtra && <div className="mt-6">{sidebarExtra}</div>}
        {sidebarFooter && <div className="mt-auto pt-6">{sidebarFooter}</div>}
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
