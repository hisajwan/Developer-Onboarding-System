"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { TextInput } from "@/components/atoms/TextInput";
import { useProjectContext } from "@/app/(app)/ProjectProvider";

/**
 * Lets a user switch between their own projects, or create a new one - shown above the nav so it
 * applies to every screen, not just Ask.
 */
export function ProjectSwitcher() {
  const { projects, currentProjectId, selectProject, createProject, isLoading, error } =
    useProjectContext();
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setIsSubmitting(true);
    try {
      await createProject(trimmed);
      setName("");
      setIsCreating(false);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <p className="px-1 text-xs text-muted">Loading projects…</p>;
  }

  // The first project is created together with its first document, in the main panel that
  // replaces the whole app until one exists (see CreateFirstProjectPanel) - nothing to switch or
  // add here yet.
  if (projects.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 px-1">
      <label className="flex flex-col gap-1 text-xs font-medium">
        Project
        <select
          value={currentProjectId ?? ""}
          onChange={(event) => selectProject(event.target.value)}
          className="w-full rounded-md border border-border bg-canvas px-2 py-1.5 text-sm outline-none focus:border-primary"
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </label>
      {isCreating ? (
        <form onSubmit={handleCreate} className="flex flex-col gap-1.5">
          <TextInput
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Project name"
            autoFocus
          />
          <div className="flex gap-1.5">
            <Button type="submit" disabled={!name.trim() || isSubmitting} className="flex-1 text-xs">
              {isSubmitting ? "Creating…" : "Create"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setIsCreating(false);
                setName("");
              }}
              className="text-xs"
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <Button variant="ghost" onClick={() => setIsCreating(true)} className="w-full text-left text-xs">
          + New project
        </Button>
      )}
      {error && (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
