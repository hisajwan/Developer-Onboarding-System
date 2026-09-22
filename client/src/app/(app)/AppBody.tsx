"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { PROJECT_EXEMPT_ROUTES } from "@/config/projectRoutes";
import { CreateProjectScreen } from "./CreateProjectScreen";
import { useProjectContext } from "./ProjectProvider";

/**
 * Gates every module screen (Dashboard, Ask, Code review) behind having a project - there is
 * nothing useful any of them can show without one - and behind the create-project screen when
 * it's been opened deliberately (see ProjectSwitcher's "+"), whatever route was actually requested.
 */
export function AppBody({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { projects, isLoading, isCreateScreenOpen } = useProjectContext();

  if (PROJECT_EXEMPT_ROUTES.includes(pathname)) return <>{children}</>;
  if (isLoading) return <p className="text-sm text-muted">Loading your projects...</p>;
  if (projects.length === 0 || isCreateScreenOpen) return <CreateProjectScreen />;

  return <>{children}</>;
}
