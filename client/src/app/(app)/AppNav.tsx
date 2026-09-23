"use client";

import { SidebarNav } from "@/components/organisms/SidebarNav";
import type { NavEntry } from "@/config/navigation";
import { useProjectContext } from "./ProjectProvider";

/**
 * The Dashboard/Ask/Code review tabs - hidden until at least one project exists, since none of
 * those screens have anything to show without one.
 */
export function AppNav({ entries }: { entries: NavEntry[] }) {
  const { projects, isLoading } = useProjectContext();

  if (isLoading || projects.length === 0) return null;

  return <SidebarNav entries={entries} />;
}
