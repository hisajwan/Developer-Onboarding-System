"use client";

import { useProjectContext } from "@/app/(app)/ProjectProvider";

/**
 * Lets a user switch between their own projects, or open the create-project screen for a new one
 * - that screen (see CreateProjectScreen) is the one and only way to create a project, so its
 * name+document requirement can't be bypassed through a simpler path here. Sits on the header's
 * left edge.
 */
export function ProjectSwitcher() {
  const { projects, currentProjectId, selectProject, openCreateScreen, isLoading, error } =
    useProjectContext();

  if (isLoading) {
    return <p className="text-xs text-muted">Loading projects…</p>;
  }

  if (projects.length === 0) return null; // CreateProjectScreen already owns the whole screen

  return (
    <div className="flex items-center gap-2">
      <select
        value={currentProjectId ?? ""}
        onChange={(event) => selectProject(event.target.value)}
        aria-label="Project"
        className="rounded-md border border-border bg-canvas px-2 py-1.5 text-sm outline-none focus:border-primary"
      >
        {currentProjectId === null && (
          <option value="" disabled>
            Select a project…
          </option>
        )}
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={openCreateScreen}
        className="whitespace-nowrap rounded-md px-2 py-1 text-xs font-medium text-muted hover:bg-surface hover:text-ink"
      >
        + New project
      </button>
      {error && <span className="text-xs text-danger">{error}</span>}
    </div>
  );
}
