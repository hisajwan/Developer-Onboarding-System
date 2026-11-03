"use client";

import { useState } from "react";
import { useProjectContext } from "@/app/(app)/ProjectProvider";
import { Select } from "@/components/atoms/Select";
import { SettingsButton } from "@/components/atoms/SettingsButton";
import { BulkDeleteModal } from "@/components/molecules/BulkDeleteModal";

/**
 * Lets a user switch between their own projects, manage (delete) them from the gear, or open the
 * create-project screen for a new one - that screen (see CreateProjectScreen) is the one and only
 * way to create a project, so its name+document requirement can't be bypassed through a simpler
 * path here. Sits on the header's left edge.
 */
export function ProjectSwitcher() {
  const {
    projects,
    currentProjectId,
    selectProject,
    deleteProjects,
    openCreateScreen,
    isLoading,
    error,
  } = useProjectContext();
  const [isManageOpen, setIsManageOpen] = useState(false);

  if (isLoading) {
    return <p className="text-xs text-muted">Loading projects…</p>;
  }

  if (projects.length === 0) return null; // CreateProjectScreen already owns the whole screen

  return (
    <div className="flex items-center gap-2">
      <SettingsButton label="Manage projects" onClick={() => setIsManageOpen(true)} />
      <Select
        size="md"
        value={currentProjectId ?? ""}
        onChange={(event) => selectProject(event.target.value)}
        aria-label="Project"
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
      </Select>
      <button
        type="button"
        onClick={openCreateScreen}
        className="whitespace-nowrap rounded-md px-2 py-1 text-xs font-medium text-muted hover:bg-surface hover:text-ink"
      >
        + New project
      </button>
      {error && <span className="text-xs text-danger">{error}</span>}
      <BulkDeleteModal
        isOpen={isManageOpen}
        onClose={() => setIsManageOpen(false)}
        title="Manage projects"
        noun={["project", "projects"]}
        items={projects.map((project) => ({
          id: project.id,
          label: project.name,
          detail: project.id === currentProjectId ? "open now" : undefined,
        }))}
        consequence="Their documents, chat sessions and dashboard history are deleted with them."
        onDelete={deleteProjects}
      />
    </div>
  );
}
