"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
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
  /** The "create a project" screen - shown full-page when there are none yet, or opened over the
   * current one on request (see ProjectSwitcher's "+"). */
  isCreateScreenOpen: boolean;
  openCreateScreen: () => void;
  closeCreateScreen: () => void;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

interface ProjectProviderProps {
  /** The signed-in user's last selected project, from the session - restored once the list loads. */
  initialProjectId: string | null;
  children: ReactNode;
}

/**
 * Holds which project is active at the layout level, so every screen (Dashboard, Ask, Code
 * review) shares one selection instead of each picking its own.
 */
export function ProjectProvider({ initialProjectId, children }: ProjectProviderProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(initialProjectId);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateScreenOpen, setIsCreateScreenOpen] = useState(false);
  // What was selected right before opening the create screen, so Cancel can put it back - a plain
  // ref, not state, since nothing ever needs to render off this value directly.
  const projectBeforeCreateScreenRef = useRef<string | null>(null);

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
    // Picking a project from the switcher is also how you back out of the create-project screen -
    // the dropdown should always return you to normal view, not just its Cancel button.
    setIsCreateScreenOpen(false);
    // Best-effort: the switch already happened locally; a failed write here only means the next
    // login restores a stale project, not something worth blocking or erroring the UI over.
    apiSelectProject(projectId).catch(() => {});
  }, []);

  const openCreateScreen = useCallback(() => {
    projectBeforeCreateScreenRef.current = currentProjectId;
    // Deselecting matters: with the previous project still "selected" in the dropdown, re-picking
    // it (the only way back when there's just one project) wouldn't fire a change event at all,
    // since as far as the <select> element is concerned nothing changed.
    setCurrentProjectId(null);
    setIsCreateScreenOpen(true);
  }, [currentProjectId]);

  const closeCreateScreen = useCallback(() => {
    setCurrentProjectId(projectBeforeCreateScreenRef.current);
    setIsCreateScreenOpen(false);
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
        isCreateScreenOpen,
        openCreateScreen,
        closeCreateScreen,
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
