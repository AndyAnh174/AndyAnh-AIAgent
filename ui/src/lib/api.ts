/**
 * API Client for AI Life Companion
 * Handles all API requests to the backend
 */

const getApiBaseUrl = () => {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("api_url");
    if (saved) return saved;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

export interface JournalEntry {
  entry_id: number;
  title: string;
  content: string;
  mood?: string;
  tags: string[];
  created_at: string;
  media?: MediaItem[];
}

export interface MediaItem {
  type: "image" | "video" | "pdf";
  url: string;
  caption?: string;
}

// Backend journal entry summary/detail types
export interface JournalEntrySummary {
  entry_id: number;
  title: string;
  mood?: string | null;
  tags: string[];
  created_at: string;
  media_count: number;
}

export interface JournalMediaInfo {
  id: number;
  type: string;
  url: string;
  storage_path: string;
  details: Record<string, unknown>;
}

export interface JournalEntryDetail {
  entry_id: number;
  title: string;
  content: string;
  mood?: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
  media: JournalMediaInfo[];
}

export interface CreateJournalRequest {
  title: string;
  content: string;
  mood?: string;
  tags?: string[];
  media?: MediaItem[];
}

export interface RetrievalRequest {
  query: string;
  top_k?: number;
  mode?: "graph" | "hybrid";
  model?: "gemini" | "openai" | "ollama" | null;
  ollama_model?: string | null;
}

export interface RetrievalResponse {
  answer: string;
  references: Array<{
    entry_id: number;
    tags: string[];
  }>;
}

export interface Reminder {
  reminder_id: number;
  entry_id?: number;
  email: string;
  subject: string;
  body: string;
  cadence: "once" | "daily" | "weekly" | "monthly" | "yearly";
  first_run_at: string;
  next_run_at: string;
}

export interface CreateReminderRequest {
  entry_id?: number;
  email: string;
  subject: string;
  body: string;
  cadence?: "once" | "daily" | "weekly" | "monthly" | "yearly";
  first_run_at: string;
}

class ApiClient {
  private apiKey: string | null = null;

  setApiKey(key: string) {
    this.apiKey = key;
    if (typeof window !== "undefined") {
      localStorage.setItem("api_key", key);
    }
  }

  getApiKey(): string | null {
    if (this.apiKey) return this.apiKey;
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("api_key");
      if (stored) {
        this.apiKey = stored;
        return stored;
      }
    }
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const apiKey = this.getApiKey();
    if (!apiKey && endpoint !== "/health") {
      throw new Error("API key is required");
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (apiKey) {
      headers["x-api-key"] = apiKey;
    }

    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const error = await response.json();
        // Try to extract error message from various possible formats
        errorMessage = 
          (error.detail as string) || 
          (error.message as string) || 
          ((error.error as { message?: string })?.message) || 
          (Array.isArray(error.detail) ? error.detail.map((e: { msg?: string; message?: string }) => e.msg || e.message).join(", ") : (error.detail as string)) ||
          response.statusText;
      } catch {
        // If JSON parsing fails, use status text
        errorMessage = response.statusText;
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.request("/health");
  }

  async createJournalEntry(
    data: CreateJournalRequest
  ): Promise<{ entry_id: number; created_at: string; tags: string[] }> {
    return this.request("/journal", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async queryJournal(
    data: RetrievalRequest
  ): Promise<RetrievalResponse> {
    return this.request("/retrieval", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async createReminder(
    data: CreateReminderRequest
  ): Promise<{ reminder_id: number; next_run_at: string; cadence: string }> {
    return this.request("/reminders", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Journal management (CRUD)
  async listJournalEntries(params?: {
    limit?: number | null;
    offset?: number;
    sort_by?: "title" | "created_at";
    sort_order?: "asc" | "desc";
    date_from?: string; // YYYY-MM-DD
    date_to?: string; // YYYY-MM-DD
  }): Promise<JournalEntrySummary[]> {
    const searchParams = new URLSearchParams();
    if (params?.limit !== undefined && params.limit !== null) {
      searchParams.set("limit", String(params.limit));
    }
    if (params?.offset) searchParams.set("offset", String(params.offset));
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params?.sort_order) searchParams.set("sort_order", params.sort_order);
    if (params?.date_from) searchParams.set("date_from", params.date_from);
    if (params?.date_to) searchParams.set("date_to", params.date_to);
    const query = searchParams.toString();
    const path = query ? `/journal?${query}` : "/journal";
    return this.request(path);
  }

  async getJournalEntry(entryId: number): Promise<JournalEntryDetail> {
    return this.request(`/journal/${entryId}`);
  }

  async updateJournalEntry(
    entryId: number,
    data: Partial<Pick<CreateJournalRequest, "title" | "content" | "mood" | "tags">>
  ): Promise<JournalEntryDetail> {
    return this.request(`/journal/${entryId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteJournalEntry(entryId: number): Promise<void> {
    await this.request(`/journal/${entryId}`, {
      method: "DELETE",
    });
  }

  async getAnalysisSummary(limit = 200): Promise<{
    mood_trend: Array<{ date: string; mood: string; score: number | null }>;
    mood_frequency: Record<string, number>;
    top_topics: Array<{ topic: string; count: number }>;
    insights: Array<{ title: string; description: string }>;
    last_updated: string;
  }> {
    const params = new URLSearchParams({ limit: String(limit) });
    return this.request(`/analysis/summary?${params.toString()}`);
  }

  async listOllamaModels(baseUrl?: string): Promise<Array<{ name: string; model: string }>> {
    const ollamaUrl = baseUrl || this.getOllamaBaseUrl();
    try {
      const response = await fetch(`${ollamaUrl}/api/tags`);
      if (!response.ok) {
        throw new Error("Failed to fetch Ollama models");
      }
      const data = await response.json();
      // Ollama API returns models in format: { models: [{ name: "...", ... }] }
      return (data.models || []).map((m: { name: string }) => ({
        name: m.name,
        model: m.name,
      }));
    } catch (error) {
      console.error("Error fetching Ollama models:", error);
      throw error;
    }
  }

  getOllamaBaseUrl(): string {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("ollama_base_url");
      if (saved) return saved;
    }
    return process.env.NEXT_PUBLIC_OLLAMA_URL || "http://222.253.80.30:11434";
  }

  setOllamaBaseUrl(url: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("ollama_base_url", url);
    }
  }

  getOllamaVisionModel(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("ollama_vision_model");
    }
    return null;
  }

  setOllamaVisionModel(model: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("ollama_vision_model", model);
    }
  }

  async searchEntries(params: {
    query: string;
    has_media?: boolean;
    media_type?: "image" | "video" | "pdf";
    limit?: number;
  }): Promise<{
    query: string;
    count: number;
    results: Array<{
      entry_id: number;
      title: string;
      content: string;
      mood?: string;
      tags: string[];
      created_at: string;
      media: Array<{
        id: number;
        type: string;
        url: string;
        storage_path: string;
        details: Record<string, unknown>;
      }>;
    }>;
  }> {
    const searchParams = new URLSearchParams({
      query: params.query,
      ...(params.has_media !== undefined && { has_media: String(params.has_media) }),
      ...(params.media_type && { media_type: params.media_type }),
      ...(params.limit && { limit: String(params.limit) }),
    });
    return this.request(`/search?${searchParams.toString()}`);
  }

  async clearAllData(confirm: boolean = false): Promise<{ status: string; message: string }> {
    return this.request("/admin/clear", {
      method: "POST",
      body: JSON.stringify({ confirm }),
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  async getStats(): Promise<{
    total_entries: number;
    total_media: number;
    entries_with_media: number;
    media_by_type: Record<string, number>;
  }> {
    return this.request("/admin/stats");
  }

  getMediaUrl(mediaId: number): string {
    const baseUrl = getApiBaseUrl();
    return `${baseUrl}/api/media/${mediaId}`;
  }
}

export const apiClient = new ApiClient();
