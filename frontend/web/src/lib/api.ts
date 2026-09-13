const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface CitationSource {
  source: string;
  snippet: string;
  source_type: "document" | "web";
  url?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  sender: "user" | "assistant";
  content: string;
  sources: CitationSource[];
  route_taken?: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentRecord {
  doc_id: string;
  filename: string;
  filepath: string;
  file_size_bytes: number;
  chunk_count: number;
  status: string;
  created_at?: string;
}

export interface QueryResponse {
  answer: string;
  filepath: string;
  sources: CitationSource[];
  route_taken: string;
  session_id: string;
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("rag_token");
}

export function setAuthToken(token: string, username: string, isAdmin = false): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("rag_token", token);
  localStorage.setItem("rag_username", username);
  localStorage.setItem("rag_is_admin", isAdmin ? "true" : "false");
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("rag_token");
  localStorage.removeItem("rag_username");
  localStorage.removeItem("rag_is_admin");
}

export function getStoredUsername(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("rag_username");
}

export function getStoredIsAdmin(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("rag_is_admin") === "true";
}

function getHeaders(extra: HeadersInit = {}): HeadersInit {
  const token = getAuthToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

export async function loginUser(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

export async function registerUser(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export async function fetchSessions(): Promise<ChatSession[]> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    headers: getHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function createSession(title = "New Conversation"): Promise<ChatSession> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: getHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  return res.ok;
}

export async function fetchSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
    headers: getHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function sendQuery(prompt: string, sessionId?: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/rag/query`, {
    method: "POST",
    headers: getHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ prompt, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Query failed: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchDocuments(): Promise<DocumentRecord[]> {
  const res = await fetch(`${API_BASE}/rag/documents`, {
    headers: getHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.documents || [];
}

export async function uploadDocument(file: File): Promise<{ job_id: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/rag/upload`, {
    method: "POST",
    headers: getHeaders(),
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "File upload failed");
  }
  return res.json();
}

export async function pollUploadStatus(jobId: string): Promise<{ status: string; error?: string }> {
  const res = await fetch(`${API_BASE}/rag/upload-status/${jobId}`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Job not found");
  return res.json();
}

export async function deleteDocument(docId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/rag/documents/${docId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  return res.ok;
}

export async function resetKnowledgeBase(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/rag/reset`, {
    method: "POST",
    headers: getHeaders(),
  });
  return res.ok;
}

export async function runEvaluation(): Promise<any> {
  const res = await fetch(`${API_BASE}/admin/evaluate`, {
    method: "POST",
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Evaluation benchmark failed");
  }
  return res.json();
}
