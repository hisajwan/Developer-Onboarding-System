"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { APP_NAME } from "@/config/app";
import { PROJECT_EXEMPT_ROUTES } from "@/config/projectRoutes";
import { cn } from "@/lib/cn";

const SIDEBAR_COLLAPSE_KEY = "sidebar-collapsed";
const DOCS_COLLAPSE_KEY = "docs-panel-collapsed";

/**
 * A collapsed/expanded flag, remembered in localStorage, defaulting to collapsed under
 * `defaultNarrowBelowPx` on a viewer's very first visit.
 */
function useCollapsible(storageKey: string, defaultNarrowBelowPx: number) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    function applyInitial() {
      try {
        const stored = window.localStorage.getItem(storageKey);
        if (stored !== null) {
          setIsCollapsed(stored === "true");
          return;
        }
      } catch {
        // Falls through to the width-based default (private mode, blocked storage, etc.).
      }
      setIsCollapsed(window.innerWidth < defaultNarrowBelowPx);
    }
    applyInitial();
    // storageKey/defaultNarrowBelowPx are constants passed by the caller, not reactive inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggle() {
    setIsCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(storageKey, String(next));
      } catch {
        // Per-viewer convenience only; losing the preference is fine.
      }
      return next;
    });
  }

  return [isCollapsed, toggle] as const;
}

function Hamburger() {
  return (
    <span className="flex shrink-0 flex-col gap-1">
      <span className="block h-0.5 w-4 bg-ink" />
      <span className="block h-0.5 w-4 bg-ink" />
      <span className="block h-0.5 w-4 bg-ink" />
    </span>
  );
}

interface AppShellProps {
  /** The Dashboard/Ask/Code review links - hidden by the caller until there's a project. */
  nav: ReactNode;
  /** The project switcher, on the header's left edge. */
  projectSwitcher?: ReactNode;
  /**
   * The project's documents - a right-hand column on desktop, stacked below content on mobile;
   * collapsible via the header's own toggle on the right.
   */
  docsPanel?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
}

export function AppShell({ nav, projectSwitcher, docsPanel, footer, children }: AppShellProps) {
  const pathname = usePathname();
  const [isSidebarCollapsed, toggleSidebar] = useCollapsible(SIDEBAR_COLLAPSE_KEY, 768);
  const [isDocsCollapsed, toggleDocs] = useCollapsible(DOCS_COLLAPSE_KEY, 1024);
  // Account settings aren't project-scoped, so the project switcher and docs panel/toggle have
  // nothing meaningful to show there.
  const showProjectChrome = !PROJECT_EXEMPT_ROUTES.includes(pathname);
  const showDocs = showProjectChrome && docsPanel;

  return (
    // The shell is pinned to the viewport height; only the regions below that declare their own
    // overflow (main's content, and the docs panel) scroll — the outer frame never does.
    <div className="flex h-screen overflow-hidden">
      <aside
        className={cn(
          "flex shrink-0 flex-col overflow-hidden bg-surface transition-[width] duration-150",
          isSidebarCollapsed ? "w-12 items-center p-2" : "w-56 p-4",
        )}
      >
        <div
          className={cn("flex items-center", isSidebarCollapsed ? "justify-center" : "justify-between")}
        >
          {!isSidebarCollapsed && <p className="whitespace-nowrap text-sm font-bold">{APP_NAME}</p>}
          <button
            type="button"
            onClick={toggleSidebar}
            aria-label={isSidebarCollapsed ? "Show sidebar" : "Hide sidebar"}
            title={isSidebarCollapsed ? "Show sidebar" : "Hide sidebar"}
            className="rounded-md p-2 hover:bg-canvas"
          >
            <Hamburger />
          </button>
        </div>
        {!isSidebarCollapsed && (
          <>
            <div className="mt-6">{nav}</div>
            {footer && <div className="mt-auto pt-6">{footer}</div>}
          </>
        )}
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-border bg-canvas px-4 py-3 sm:px-6">
          <div className="min-w-0 flex-1">{showProjectChrome && projectSwitcher}</div>
          {showDocs && (
            <button
              type="button"
              onClick={toggleDocs}
              className="shrink-0 rounded-md px-2 py-1.5 text-xs font-medium text-muted hover:bg-surface hover:text-ink"
            >
              {isDocsCollapsed ? "Show docs" : "Hide docs"}
            </button>
          )}
        </header>
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto lg:flex-row lg:overflow-hidden">
          <main className="min-w-0 flex-1 p-4 sm:p-6 lg:overflow-y-auto lg:p-8">{children}</main>
          {showDocs && !isDocsCollapsed && (
            <aside className="shrink-0 border-t border-border p-4 lg:w-72 lg:overflow-y-auto lg:border-l lg:border-t-0 lg:p-6">
              {docsPanel}
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
