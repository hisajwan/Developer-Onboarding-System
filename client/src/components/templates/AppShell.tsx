import type { ReactNode } from "react";
import { APP_NAME } from "@/config/app";

interface AppShellProps {
  /** The project switcher: applies to every screen, so it sits above the nav, not below it. */
  sidebarTop?: ReactNode;
  sidebar: ReactNode;
  /** Page-specific sidebar content (e.g. the Ask screen's docs upload panel). Sits below the nav. */
  sidebarExtra?: ReactNode;
  sidebarFooter?: ReactNode;
  children: ReactNode;
}

export function AppShell({
  sidebarTop,
  sidebar,
  sidebarExtra,
  sidebarFooter,
  children,
}: AppShellProps) {
  return (
    // The shell is pinned to the viewport height; only the regions below that declare their own
    // overflow (main's content, and the docs upload list) scroll — the sidebar never does.
    <div className="flex h-screen overflow-hidden">
      <aside className="flex w-56 shrink-0 flex-col bg-surface p-4">
        <p className="mb-6 px-1 text-sm font-bold">{APP_NAME}</p>
        {sidebarTop && <div className="mb-6">{sidebarTop}</div>}
        {sidebar}
        {sidebarExtra && <div className="mt-6">{sidebarExtra}</div>}
        {sidebarFooter && <div className="mt-auto pt-6">{sidebarFooter}</div>}
      </aside>
      <main className="min-h-0 flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
