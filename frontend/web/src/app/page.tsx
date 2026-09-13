"use client";

import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import DocumentsView from "@/components/DocumentsView";
import ObservabilityView from "@/components/ObservabilityView";
import AboutView from "@/components/AboutView";
import AuthModal from "@/components/AuthModal";
import {
  ChatSession,
  ChatMessage,
  DocumentRecord,
  fetchSessions,
  createSession,
  deleteSession,
  fetchSessionMessages,
  sendQuery,
  fetchDocuments,
  getStoredUsername,
  getStoredIsAdmin,
  clearAuthToken,
} from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "documents" | "observability" | "about">("chat");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  // Initialize Auth state
  useEffect(() => {
    const user = getStoredUsername();
    if (user) {
      setUsername(user);
      setIsAdmin(getStoredIsAdmin());
    }
  }, []);

  // Load Sessions
  const loadSessions = useCallback(async () => {
    if (!username) return;
    try {
      const list = await fetchSessions();
      setSessions(list);
      if (list.length > 0 && !activeSessionId) {
        setActiveSessionId(list[0].id);
      }
    } catch {
      // ignore
    }
  }, [username, activeSessionId]);

  // Load Documents
  const loadDocuments = useCallback(async () => {
    if (!username) return;
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch {
      // ignore
    }
  }, [username]);

  // Load Messages for active session
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }
    fetchSessionMessages(activeSessionId).then(setMessages);
  }, [activeSessionId]);

  useEffect(() => {
    if (username) {
      loadSessions();
      loadDocuments();
    }
  }, [username, loadSessions, loadDocuments]);

  // Create New Chat
  const handleNewChat = async () => {
    if (!username) {
      setAuthModalOpen(true);
      return;
    }
    try {
      const newSession = await createSession("New Conversation");
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
    } catch (err) {
      console.error(err);
    }
  };

  // Delete Session
  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId);
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Send Query
  const handleSend = async (prompt: string) => {
    if (!username) {
      setAuthModalOpen(true);
      return;
    }

    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      try {
        const newSession = await createSession(prompt.slice(0, 30));
        currentSessionId = newSession.id;
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
      } catch (err) {
        console.error(err);
        return;
      }
    }

    // Optimistic user message
    const tempUserMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      session_id: currentSessionId,
      sender: "user",
      content: prompt,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await sendQuery(prompt, currentSessionId);
      const assistantMsg: ChatMessage = {
        id: "msg-" + Date.now(),
        session_id: currentSessionId,
        sender: "assistant",
        content: res.answer,
        sources: res.sources,
        route_taken: res.route_taken,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      loadSessions(); // refresh title if updated
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: "err-" + Date.now(),
        session_id: currentSessionId,
        sender: "assistant",
        content: `Error: ${err.message || "Failed to process request"}`,
        sources: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    setUsername(null);
    setIsAdmin(false);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
    setDocuments([]);
    if (activeTab === "observability") {
      setActiveTab("chat");
    }
  };

  const activeSessionTitle =
    sessions.find((s) => s.id === activeSessionId)?.title || "New Conversation";

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100">
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        username={username}
        isAdmin={isAdmin}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Content Area - views stay mounted so background uploads/timers are never destroyed */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <div className={activeTab === "chat" ? "h-full w-full flex flex-col" : "hidden"}>
          <ChatArea
            messages={messages}
            loading={loading}
            onSend={handleSend}
            activeSessionTitle={activeSessionTitle}
            documentCount={documents.length}
            onNavigateToDocuments={() => setActiveTab("documents")}
          />
        </div>

        <div className={activeTab === "documents" ? "h-full w-full flex flex-col overflow-hidden" : "hidden"}>
          <DocumentsView
            documents={documents}
            onRefresh={loadDocuments}
            username={username}
            onOpenAuth={() => setAuthModalOpen(true)}
          />
        </div>

        <div className={activeTab === "observability" ? "h-full w-full flex flex-col overflow-hidden" : "hidden"}>
          {activeTab === "observability" && <ObservabilityView />}
        </div>

        <div className={activeTab === "about" ? "h-full w-full flex flex-col overflow-hidden" : "hidden"}>
          <AboutView />
        </div>
      </main>

      {/* Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(user, admin) => {
          setUsername(user);
          setIsAdmin(Boolean(admin));
        }}
      />
    </div>
  );
}
