"use client";

import type { ReactNode } from "react";
import { CreateFirstProjectPanel } from "./CreateFirstProjectPanel";
import { useProjectContext } from "./ProjectProvider";

/**
 * Gates every screen (Dashboard, Ask, Code review) behind having a project - there is nothing
 * useful any of them can show without one, whatever route was actually requested.
 */
export function AppBody({ children }: { children: ReactNode }) {
  const { projects, isLoading } = useProjectContext();

  if (isLoading) return <p className="text-sm text-muted">Loading your projects...</p>;
  if (projects.length === 0) return <CreateFirstProjectPanel />;

  return <>{children}</>;
}
