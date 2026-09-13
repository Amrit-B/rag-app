"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChatMessage, CitationSource } from "@/lib/api";
import {
  Send,
  Sparkles,
  Database,
  Globe,
  FileText,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Bot,
  User as UserIcon,
  Loader2,
  Layers,
} from "lucide-react";

interface ChatAreaProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (prompt: string) => void;
  activeSessionTitle: string;
}

const STEP_LABELS = [
  "Routing query with Router Chain...",
  "Querying LanceDB vector store...",
  "Grading document relevance...",
  "Assessing context & web search need...",
  "Synthesizing grounded answer...",
  "Verifying groundedness (Hallucination check)...",
];

export default function ChatArea({
  messages,
  loading,
  onSend,
  activeSessionTitle,
}: ChatAreaProps) {
  const [input, setInput] = useState("");
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [openSourcesId, setOpenSourcesId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cycle animated step label while loading
  useEffect(() => {
    if (!loading) {
      setActiveStepIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setActiveStepIndex((prev) => (prev + 1) % STEP_LABELS.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [loading]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const prompt = input.trim();
    setInput("");
    onSend(prompt);
  };

  const toggleSources = (msgId: string) => {
    setOpenSourcesId((prev) => (prev === msgId ? null : msgId));
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-900 text-slate-100 overflow-hidden">
      {/* Top Bar */}
      <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/90 backdrop-blur-md shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></div>
          <h2 className="text-sm font-semibold text-white truncate max-w-md">
            {activeSessionTitle || "New Conversation"}
          </h2>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span className="hidden sm:inline bg-slate-800 px-2.5 py-1 rounded-md border border-slate-700">
            Engine: Gemini 2.5 Flash + LanceDB
          </span>
        </div>
      </header>

      {/* Message History */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4 max-w-xl mx-auto space-y-6 animate-in fade-in duration-300">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-xl shadow-indigo-500/20">
              <Sparkles className="w-7 h-7" />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-white tracking-tight">
                Self-Reflective Agentic RAG
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Ask questions against your uploaded PDFs. The pipeline uses LangGraph to evaluate document relevance, falls back to live Tavily web search when necessary, and self-checks for hallucinations.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
              {[
                "What are the main topics in my uploaded documents?",
                "Summarize the technical architecture described.",
                "Compare section 2 with current industry standards.",
                "Extract all key metrics and numbers.",
              ].map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSend(prompt)}
                  className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/80 hover:border-indigo-500/50 hover:bg-slate-800 text-xs text-slate-300 hover:text-white transition-all text-left"
                >
                  &ldquo;{prompt}&rdquo;
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === "user";
            const sources = msg.sources || [];
            const isSourcesOpen = openSourcesId === msg.id;

            return (
              <div
                key={msg.id}
                className={`flex space-x-3 max-w-3xl ${
                  isUser ? "ml-auto justify-end" : "mr-auto justify-start"
                }`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`space-y-2 max-w-2xl ${isUser ? "text-right" : "text-left"}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      isUser
                        ? "bg-indigo-600 text-white rounded-br-sm shadow-md"
                        : "bg-slate-800/90 text-slate-200 border border-slate-700/80 rounded-bl-sm shadow-sm"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  </div>

                  {!isUser && (
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      {/* Route Taken Badge */}
                      {msg.route_taken && (
                        <span
                          className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
                            msg.route_taken === "websearch"
                              ? "bg-amber-950/40 border-amber-800 text-amber-300"
                              : msg.route_taken === "hybrid"
                              ? "bg-purple-950/40 border-purple-800 text-purple-300"
                              : "bg-indigo-950/40 border-indigo-800 text-indigo-300"
                          }`}
                        >
                          {msg.route_taken === "websearch" ? (
                            <Globe className="w-3 h-3" />
                          ) : msg.route_taken === "hybrid" ? (
                            <Layers className="w-3 h-3" />
                          ) : (
                            <Database className="w-3 h-3" />
                          )}
                          <span className="capitalize">{msg.route_taken}</span>
                        </span>
                      )}

                      {/* Sources Toggle Button */}
                      {sources.length > 0 && (
                        <button
                          onClick={() => toggleSources(msg.id)}
                          className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                        >
                          <FileText className="w-3 h-3 text-indigo-400" />
                          <span>{sources.length} Cited Sources</span>
                          {isSourcesOpen ? (
                            <ChevronUp className="w-3 h-3" />
                          ) : (
                            <ChevronDown className="w-3 h-3" />
                          )}
                        </button>
                      )}
                    </div>
                  )}

                  {/* Expandable Citations Drawer */}
                  {!isUser && isSourcesOpen && sources.length > 0 && (
                    <div className="mt-2 space-y-2 rounded-xl bg-slate-950/80 border border-slate-800 p-3 text-xs text-left animate-in fade-in duration-200">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        Retrieved & Graded Context
                      </div>
                      <div className="grid grid-cols-1 gap-2">
                        {sources.map((src, i) => (
                          <div
                            key={i}
                            className="rounded-lg bg-slate-900 border border-slate-800/80 p-2.5 space-y-1 hover:border-slate-700 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-indigo-300 truncate max-w-xs flex items-center space-x-1.5">
                                {src.source_type === "web" ? (
                                  <Globe className="w-3.5 h-3.5 text-amber-400" />
                                ) : (
                                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                                )}
                                <span className="truncate">{src.source}</span>
                              </span>
                              {src.url && (
                                <a
                                  href={src.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-[10px] text-indigo-400 hover:underline flex items-center space-x-1"
                                >
                                  <span>Visit</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-400 italic line-clamp-3">
                              &ldquo;{src.snippet}&rdquo;
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 shrink-0 mt-0.5">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Live LangGraph Step Indicator */}
        {loading && (
          <div className="flex items-center space-x-3 text-left animate-in fade-in duration-200">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shrink-0">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="rounded-2xl bg-slate-800/80 border border-slate-700/80 px-4 py-2.5 flex items-center space-x-2 text-xs text-indigo-300 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
              <span className="font-medium">{STEP_LABELS[activeStepIndex]}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/80 shrink-0">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask a question about your knowledge base or technical documents..."
            className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-3 text-white shadow-md shadow-indigo-600/30 transition-all disabled:opacity-50 flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="max-w-3xl mx-auto mt-1.5 flex items-center justify-between text-[11px] text-slate-500 px-1">
          <span>Enter to submit • Uses LangGraph Corrective RAG</span>
          <span>SQLite session persistence enabled</span>
        </div>
      </div>
    </div>
  );
}
