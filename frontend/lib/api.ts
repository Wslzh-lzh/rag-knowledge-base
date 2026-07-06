export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const TOKEN_KEY = "rag_access_token";

export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  status: string;
  role: string;
  created_at?: string;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  visibility: string;
  owner_id: string;
  settings: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface Document {
  id: string;
  kb_id: string;
  uploader_id: string;
  file_name: string;
  file_type: string;
  mime_type: string;
  sha256: string;
  storage_uri: string;
  parse_status: string;
  metadata_: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  kb_id: string;
  parent_chunk_id: string | null;
  chunk_no: number;
  content: string;
  page_start: number | null;
  page_end: number | null;
  token_count: number;
  metadata_: Record<string, any>;
}

export interface SearchHit {
  chunk_id: string;
  document_id: string;
  document_name: string;
  kb_id: string;
  page_start: number | null;
  page_end: number | null;
  content: string;
  similarity_score: number;
  source_type: string;
  metadata: Record<string, any>;
}

export interface QAResponse {
  answer: string;
  citations: SearchHit[];
  usage: Record<string, any>;
  retrieval_debug: Record<string, any>;
}

export interface Conversation {
  id: string;
  kb_id: string | null;
  user_id: string;
  title: string;
  summary: string | null;
  mode: string;
  created_at?: string;
  updated_at?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  citations: any[];
  usage: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed: ${res.status} ${text}`);
  }

  if (res.status === 204) {
    return undefined as unknown as T;
  }

  const text = await res.text();
  if (!text) {
    return undefined as unknown as T;
  }
  return JSON.parse(text) as T;
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string, display_name?: string) =>
    request<UserProfile>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name }),
    }),

  me: () =>
    request<UserProfile>("/auth/me", {
      method: "GET",
    }),

  // Knowledge Bases
  listKnowledgeBases: () =>
    request<KnowledgeBase[]>("/knowledge-bases", {
      method: "GET",
    }),

  createKnowledgeBase: (name: string, description?: string, visibility: string = "private") =>
    request<KnowledgeBase>("/knowledge-bases", {
      method: "POST",
      body: JSON.stringify({ name, description, visibility }),
    }),

  getKnowledgeBase: (kbId: string) =>
    request<KnowledgeBase>(`/knowledge-bases/${kbId}`, {
      method: "GET",
    }),

  updateKnowledgeBase: (kbId: string, data: Partial<{ name: string; description: string; visibility: string }>) =>
    request<KnowledgeBase>(`/knowledge-bases/${kbId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteKnowledgeBase: (kbId: string) =>
    request<{ kb_id: string; status: string }>(`/knowledge-bases/${kbId}`, {
      method: "DELETE",
    }),

  // Documents
  listDocuments: (kbId: string) =>
    request<Document[]>(`/knowledge-bases/${kbId}/documents`, {
      method: "GET",
    }),

  uploadDocument: (kbId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<Document>(`/knowledge-bases/${kbId}/documents`, {
      method: "POST",
      body: formData,
    });
  },

  getDocument: (docId: string) =>
    request<Document>(`/documents/${docId}`, {
      method: "GET",
    }),

  listDocumentChunks: (docId: string) =>
    request<DocumentChunk[]>(`/documents/${docId}/chunks`, {
      method: "GET",
    }),

  getDocumentPreview: (docId: string) =>
    request<{
      document_id: string;
      file_name: string;
      file_type: string;
      mime_type: string;
      parse_status: string;
      total_chunks: number;
      preview: string;
      metadata: Record<string, any>;
    }>(`/documents/${docId}/preview`, {
      method: "GET",
    }),

  reprocessDocument: (docId: string) =>
    request<{ document_id: string; status: string }>(`/documents/${docId}/reprocess`, {
      method: "POST",
    }),

  deleteDocument: (docId: string) =>
    request<void>(`/documents/${docId}`, {
      method: "DELETE",
    }),

  renameDocument: (docId: string, fileName: string) =>
    request<Document>(`/documents/${docId}/rename`, {
      method: "PATCH",
      body: JSON.stringify({ file_name: fileName }),
      headers: { "Content-Type": "application/json" },
    }),

  updateDocumentContent: (docId: string, content: string) =>
    request<{ document_id: string; status: string }>(`/documents/${docId}/content`, {
      method: "PUT",
      body: JSON.stringify({ content }),
      headers: { "Content-Type": "application/json" },
    }),

  // Search
  search: (query: string, top_k: number = 10, kb_ids?: string[]) => {
    const params = new URLSearchParams({ query, top_k: String(top_k) });
    if (kb_ids?.length) {
      kb_ids.forEach((id) => params.append("kb_ids", id));
    }
    return request<SearchHit[]>(`/search?${params.toString()}`, {
      method: "GET",
    });
  },

  // QA
  askQuestion: (kbId: string, query: string, top_k: number = 5) =>
    request<QAResponse>(`/knowledge-bases/${kbId}/qa`, {
      method: "POST",
      body: JSON.stringify({ query, top_k }),
    }),

  askStream: async function* (
    kbId: string,
    query: string,
    top_k: number = 5,
  ): AsyncGenerator<{ type: string; [key: string]: any }> {
    const token = getToken();
    const res = await fetch(`${API_BASE_URL}/knowledge-bases/${kbId}/qa/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ query, top_k }),
      cache: "no-store",
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Request failed: ${res.status} ${text}`);
    }

    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          try {
            const parsed = JSON.parse(data);
            yield parsed;
          } catch (e) {
            // skip parse errors
          }
        }
      }
    }
  },

  // Conversations
  listConversations: () =>
    request<Conversation[]>("/conversations", {
      method: "GET",
    }),

  createConversation: (kb_id?: string, title?: string, mode: string = "rag") =>
    request<Conversation>("/conversations", {
      method: "POST",
      body: JSON.stringify({ kb_id, title, mode }),
    }),

  getConversation: (convId: string) =>
    request<Conversation>(`/conversations/${convId}`, {
      method: "GET",
    }),

  updateConversation: (convId: string, data: Partial<{ title: string; summary: string }>) =>
    request<Conversation>(`/conversations/${convId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteConversation: (convId: string) =>
    request<{ conversation_id: string; status: string }>(`/conversations/${convId}`, {
      method: "DELETE",
    }),

  listMessages: (convId: string) =>
    request<Message[]>(`/conversations/${convId}/messages`, {
      method: "GET",
    }),

  sendMessage: (convId: string, content: string) =>
    request<Message>(`/conversations/${convId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  sendMessageStream: async function* (
    convId: string,
    content: string,
  ): AsyncGenerator<{ type: string; [key: string]: any }> {
    const token = getToken();
    const res = await fetch(`${API_BASE_URL}/conversations/${convId}/messages/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content }),
      cache: "no-store",
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Request failed: ${res.status} ${text}`);
    }

    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          try {
            const parsed = JSON.parse(data);
            yield parsed;
          } catch (e) {
            // skip parse errors
          }
        }
      }
    }
  },
};
