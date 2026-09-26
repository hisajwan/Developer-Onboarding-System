import type { ProjectStats } from "@/types/stats";
import { apiFetch } from "./http";

export function getProjectStats(projectId: string): Promise<ProjectStats> {
  return apiFetch<ProjectStats>(`/projects/${projectId}/stats`);
}
