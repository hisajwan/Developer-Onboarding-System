import type { Project } from "@/types/project";
import { apiFetch } from "./http";

export async function listProjects(): Promise<Project[]> {
  const { projects } = await apiFetch<{ projects: Project[] }>("/projects");
  return projects;
}

export function createProject(name: string): Promise<Project> {
  return apiFetch<Project>("/projects", { method: "POST", body: JSON.stringify({ name }) });
}

export function renameProject(projectId: string, name: string): Promise<Project> {
  return apiFetch<Project>(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function selectProject(projectId: string): Promise<Project> {
  return apiFetch<Project>(`/projects/${projectId}/select`, { method: "POST" });
}
