"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import {
  createProject as apiCreateProject,
  listProjects,
  renameProject as apiRenameProject,
  selectProject as apiSelectProject,
} from "@/lib/api/projects";
import type { Project } from "@/types/project";

interface ProjectContextValue {
  projects: Project[];
  currentProjectId: string | null;
  currentProject: Project | null;
  isLoading: boolean;
  error: string | null;
  selectProject: (projectId: string) => void;
  createProject: (name: string) => Promise<Project>;
  renameProject: (projectId: string, name: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

interface ProjectProviderProps {
  /** The signed-in user's last selected project, from the session - restored once the list loads. */
  initialProjectId: string | null;
  children: ReactNode;
}

/**
 * Holds which project is active at the layout level, so every screen (Ask, its docs panel, and
 * later Code review/Dashboard) shares one selection instead of each picking its own.
 */
export function ProjectProvider({ initialProjectId, children }: ProjectProviderProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(initialProjectId);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listProjects()
      .then((list) => {
        if (cancelled) return;
        setProjects(list);
        // Keep the restored selection only if it still exists; otherwise fall back to the first
        // project, or to no selection at all for a brand new account with none yet.
        setCurrentProjectId((current) =>
          current && list.some((project) => project.id === current) ? current : (list[0]?.id ?? null),
        );
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load projects.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectProject = useCallback((projectId: string) => {
    setCurrentProjectId(projectId);
    // Best-effort: the switch already happened locally; a failed write here only means the next
    // login restores a stale project, not something worth blocking or erroring the UI over.
    apiSelectProject(projectId).catch(() => {});
  }, []);

  const createProject = useCallback(
    async (name: string) => {
      const project = await apiCreateProject(name);
      setProjects((current) => [project, ...current]);
      selectProject(project.id);
      return project;
    },
    [selectProject],
  );

  const renameProject = useCallback(async (projectId: string, name: string) => {
    const renamed = await apiRenameProject(projectId, name);
    setProjects((current) => current.map((project) => (project.id === projectId ? renamed : project)));
  }, []);

  const currentProject = projects.find((project) => project.id === currentProjectId) ?? null;

  return (
    <ProjectContext.Provider
      value={{
        projects,
        currentProjectId,
        currentProject,
        isLoading,
        error,
        selectProject,
        createProject,
        renameProject,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProjectContext(): ProjectContextValue {
  const context = useContext(ProjectContext);
  if (!context) throw new Error("useProjectContext must be used within ProjectProvider.");
  return context;
}
