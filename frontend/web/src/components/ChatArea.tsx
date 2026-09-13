"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChatMessage, CitationSource } from "@/lib/api";
import ReactMarkdown from "react-markdown";
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
  AlertCircle,
  CheckCircle2,
  UploadCloud,
  ShieldCheck,
  Cpu,
  ArrowRight,
} from "lucide-react";

interface ChatAreaProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (prompt: string) => void;
  activeSessionTitle: string;
  documentCount?: number;
  onNavigateToDocuments?: () => void;
}

const STEP_LABELS = [
  "Routing query with Router Chain...",
  "Querying LanceDB vector store...",
  "Grading document relevance (batch evaluation)...",
  "Assessing context & web search need...",
  "Synthesizing grounded answer...",
  "Verifying groundedness (Hallucination check)...",
];

export default function ChatArea({
  messages,
  loading,
  onSend,
  activeSessionTitle,
  documentCount = 0,
  onNavigateToDocuments,
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

  const getRouteBadge = (route?: string) => {
    switch (route) {
      case "websearch":
        return {
          icon: <Globe className="w-3 h-3 text-amber-400" />,
          label: "Web Search",
          className: "bg-amber-950/40 border-amber-800 text-amber-300",
        };
      case "hybrid":
        return {
          icon: <Layers className="w-3 h-3 text-purple-400" />,
          label: "Hybrid (Docs + Web)",
          className: "bg-purple-950/40 border-purple-800 text-purple-300",
        };
      case "security":
        return {
          icon: <ShieldCheck className="w-3 h-3 text-emerald-400" />,
          label: "Security & Privacy",
          className: "bg-emerald-950/40 border-emerald-800 text-emerald-300",
        };
      case "assistant":
        return {
          icon: <Bot className="w-3 h-3 text-indigo-400" />,
          label: "Assistant Direct",
          className: "bg-indigo-950/40 border-indigo-800 text-indigo-300",
        };
      case "knowledge_base":
        return {
          icon: <Database className="w-3 h-3 text-sky-400" />,
          label: "Knowledge Base",
          className: "bg-sky-950/40 border-sky-800 text-sky-300",
        };
      default:
        return {
          icon: <Database className="w-3 h-3 text-indigo-400" />,
          label: "Vector Store",
          className: "bg-indigo-950/40 border-indigo-800 text-indigo-300",
        };
    }
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

      {/* Message History / Empty Homepage State */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.length === 0 ? (
          <div className="max-w-3xl mx-auto space-y-6 py-4 animate-in fade-in duration-300">
            {/* Hero Header */}
            <div className="text-center space-y-3">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Self-Reflective Agentic RAG • LangGraph & LanceDB</span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Agentic Knowledge & Research Assistant
              </h3>
              <p className="text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed">
                An enterprise-grade retrieval pipeline that reasons before answering. It searches
                your LanceDB vector store, grades retrieved passages for relevance, validates citations
                to prevent hallucinations, and dynamically pulls from live Tavily web search when required.
              </p>
            </div>

            {/* Dynamic Knowledge Base Status Banner */}
            {documentCount === 0 ? (
              <div className="rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-slate-900 p-4 sm:p-5 shadow-lg shadow-amber-950/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start space-x-3.5">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-semibold text-amber-200">
                        Knowledge Base is Empty — No Documents Uploaded
                      </span>
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping hidden sm:inline-block"></span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed max-w-xl">
                      Local vector search needs documents to ground answers. Upload your PDF files (lecture slides, manuals, research papers) in the Knowledge Base to enable deep citation-grounded Q&A.
                    </p>
                  </div>
                </div>
                {onNavigateToDocuments && (
                  <button
                    onClick={onNavigateToDocuments}
                    className="shrink-0 inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs transition-all shadow-md hover:shadow-amber-500/20 active:scale-95"
                  >
                    <span>Upload Files</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ) : (
              <div className="rounded-2xl border border-emerald-500/40 bg-gradient-to-r from-emerald-950/40 via-emerald-900/20 to-slate-900 p-4 sm:p-5 shadow-lg shadow-emerald-950/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start space-x-3.5">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0 mt-0.5">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-semibold text-emerald-200">
                        Knowledge Base Active ({documentCount} Document{documentCount > 1 ? "s" : ""} Indexed)
                      </span>
                      <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed max-w-xl">
                      Your documents are chunked and embedded in LanceDB. You can ask document-grounded questions below, or ask broad queries for external web search synthesis.
                    </p>
                  </div>
                </div>
                {onNavigateToDocuments && (
                  <button
                    onClick={onNavigateToDocuments}
                    className="shrink-0 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-900/60 hover:bg-emerald-800/80 border border-emerald-700/60 text-emerald-200 text-xs font-medium transition-all"
                  >
                    <FileText className="w-3 h-3" />
                    <span>Manage Files</span>
                  </button>
                )}
              </div>
            )}

            {/* Architecture Highlights (3 Cards) */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                  <Cpu className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-semibold text-white">Self-Reflective RAG</h4>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  LangGraph agent autonomously grades retrieved passages for relevance and validates drafted answers against sources to eliminate hallucinations.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
                  <Database className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-semibold text-white">LanceDB Vector Database</h4>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Sub-millisecond similarity search using 768-dim Gemini embeddings to pinpoint exact technical concepts, code blocks, and metrics.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <Globe className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-semibold text-white">Adaptive Web Grounding</h4>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Autonomously triggers Tavily live web search to fill knowledge gaps when uploaded documents lack recent or complete context.
                </p>
              </div>
            </div>

            {/* Context-Aware Quick Starters */}
            <div className="space-y-2.5">
              <div className="text-xs font-medium text-slate-400 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Suggested prompts to get started:</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {(documentCount === 0
                  ? [
                      "How does this pipeline prevent hallucinations?",
                      "What document formats and content can I upload?",
                      "What are the latest breakthroughs in AI agent architectures?",
                      "How do I upload files and get started with document Q&A?",
                    ]
                  : [
                      "Summarize the key findings and executive takeaways",
                      "What are the main technical requirements and objectives?",
                      "Extract all key metrics, formulas, and deadlines",
                      "Compare the document's conclusions with current web research",
                    ]
                ).map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSend(prompt)}
                    className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/80 hover:border-indigo-500/50 hover:bg-slate-800 text-xs text-slate-300 hover:text-white transition-all text-left flex items-center justify-between group"
                  >
                    <span className="truncate mr-2">&ldquo;{prompt}&rdquo;</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 shrink-0 transition-colors" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === "user";
            const sources = msg.sources || [];
            const isSourcesOpen = openSourcesId === msg.id;
            const badge = getRouteBadge(msg.route_taken);

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
                    {isUser ? (
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    ) : (
                      <div className="text-left">
                        <ReactMarkdown
                          components={{
                            h1: ({ children }) => (
                              <h1 className="text-lg font-bold text-white mt-3 mb-1.5 first:mt-0">
                                {children}
                              </h1>
                            ),
                            h2: ({ children }) => (
                              <h2 className="text-base font-semibold text-white mt-2.5 mb-1 first:mt-0">
                                {children}
                              </h2>
                            ),
                            h3: ({ children }) => (
                              <h3 className="text-sm font-semibold text-indigo-300 mt-2 mb-1 first:mt-0">
                                {children}
                              </h3>
                            ),
                            p: ({ children }) => (
                              <p className="mb-2 last:mb-0 leading-relaxed text-slate-200">
                                {children}
                              </p>
                            ),
                            ul: ({ children }) => (
                              <ul className="list-disc list-outside space-y-1 mb-2 ml-4 text-slate-300">
                                {children}
                              </ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="list-decimal list-outside space-y-1 mb-2 ml-4 text-slate-300">
                                {children}
                              </ol>
                            ),
                            li: ({ children }) => (
                              <li className="leading-relaxed pl-0.5 text-slate-300">
                                {children}
                              </li>
                            ),
                            strong: ({ children }) => (
                              <strong className="font-semibold text-white">
                                {children}
                              </strong>
                            ),
                            em: ({ children }) => (
                              <em className="italic text-slate-300">
                                {children}
                              </em>
                            ),
                            hr: () => (
                              <hr className="border-slate-700/80 my-3" />
                            ),
                            code: ({ children }) => (
                              <code className="bg-slate-900/90 border border-slate-700/60 px-1.5 py-0.5 rounded text-xs font-mono text-indigo-300">
                                {children}
                              </code>
                            ),
                            pre: ({ children }) => (
                              <pre className="bg-slate-950 border border-slate-800 p-3 rounded-xl overflow-x-auto text-xs font-mono text-slate-200 my-2">
                                {children}
                              </pre>
                            ),
                            blockquote: ({ children }) => (
                              <blockquote className="border-l-2 border-indigo-500 pl-3 my-2 text-slate-400 italic">
                                {children}
                              </blockquote>
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {!isUser && (
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      {/* Route Taken Badge */}
                      {msg.route_taken && (
                        <span
                          className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium border ${badge.className}`}
                        >
                          {badge.icon}
                          <span>{badge.label}</span>
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
          <span>Enter to submit • LangGraph Self-Reflective RAG</span>
          <span>LanceDB isolated multi-tenant storage</span>
        </div>
      </div>
    </div>
  );
}
