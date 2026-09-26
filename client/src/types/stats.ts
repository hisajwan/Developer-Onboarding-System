export interface ActivityItem {
  kind: "question" | "review";
  source: "ask" | "code_review_screen";
  title: string;
  detail: string;
  finding_count: number | null;
  created_at: string;
}

export interface ProjectStats {
  questions_this_week: number;
  reviews_this_week: number;
  questions_total: number;
  reviews_total: number;
  documents_indexed: number;
  recent: ActivityItem[];
}
