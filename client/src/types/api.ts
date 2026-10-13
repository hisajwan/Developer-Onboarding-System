export interface ChatResponse {
  reply: string;
  sources: string[];
  tools_used: string[];
}

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string;
  sources: string[];
}

export interface ChatHistoryResponse {
  messages: ChatHistoryMessage[];
}
