"use client";

import React from "react";
import { ChatSession } from "@/lib/api";
import {
  MessageSquare,
  Plus,
  Trash2,
  FileText,
  Activity,
  Info,
  LogOut,
  LogIn,
  Layers,
  ExternalLink,
} from "lucide-react";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  activeTab: "chat" | "documents" | "observability" | "about";
  onTabChange: (tab: "chat" | "documents" | "observability" | "about") => void;
  username: string | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  activeTab,
  onTabChange,
  username,
  onOpenAuth,
  onLogout,
}: SidebarProps) {
  return (
    <aside className="w-72 bg-slate-950/90 border-r border-slate-800 flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight leading-none">
              Agentic RAG
            </h1>
            <span className="inline-flex items-center space-x-1 mt-1 text-[10px] text-emerald-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>LangGraph v0.2+</span>
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="p-3 border-b border-slate-800/60 space-y-1">
        <button
          onClick={() => onTabChange("chat")}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "chat"
              ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>Chat Assistant</span>
        </button>

        <button
          onClick={() => onTabChange("documents")}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "documents"
              ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Knowledge Base</span>
        </button>

        <button
          onClick={() => onTabChange("observability")}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "observability"
              ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Observability & Stats</span>
        </button>

        <button
          onClick={() => onTabChange("about")}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "about"
              ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <Info className="w-4 h-4" />
          <span>About Architecture</span>
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={() => {
            onTabChange("chat");
            onNewChat();
          }}
          className="w-full flex items-center justify-center space-x-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 py-2.5 text-xs font-semibold text-slate-200 hover:text-white transition-all shadow-sm hover:border-indigo-500/50"
        >
          <Plus className="w-4 h-4 text-indigo-400" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1 scrollbar-thin scrollbar-thumb-slate-800">
        <div className="px-2 py-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          Chat History
        </div>

        {sessions.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-slate-500 italic">
            No past conversations yet
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => {
                onTabChange("chat");
                onSelectSession(session.id);
              }}
              className={`group flex items-center justify-between px-3 py-2 rounded-lg text-xs cursor-pointer transition-all ${
                activeSessionId === session.id && activeTab === "chat"
                  ? "bg-slate-800/90 text-white font-medium border border-slate-700 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/80"
              }`}
            >
              <div className="flex items-center space-x-2.5 truncate pr-2">
                <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-500 group-hover:text-indigo-400" />
                <span className="truncate">{session.title}</span>
              </div>

              <button
                onClick={(e) => onDeleteSession(session.id, e)}
                title="Delete session"
                className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-1 rounded transition-opacity"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Observability Quick Link */}
      <div className="px-3 py-2 border-t border-slate-800/60 bg-slate-950">
        <a
          href="http://localhost:3001"
          target="_blank"
          rel="noreferrer"
          className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-indigo-950/30 border border-indigo-900/50 text-[11px] text-indigo-300 hover:bg-indigo-900/40 transition-colors"
        >
          <span className="flex items-center space-x-1.5">
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span>Grafana Dashboard</span>
          </span>
          <ExternalLink className="w-3 h-3 text-indigo-400" />
        </a>
      </div>

      {/* User Footer Section */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-900/40">
        {username ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 truncate">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-xs font-bold text-white uppercase">
                {username[0]}
              </div>
              <span className="text-xs text-slate-200 font-medium truncate">{username}</span>
            </div>
            <button
              onClick={onLogout}
              title="Sign out"
              className="text-slate-400 hover:text-red-400 p-1.5 rounded transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="w-full flex items-center justify-center space-x-2 py-2 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-xs font-medium text-indigo-300 hover:bg-indigo-600/30 transition-colors"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In / Register</span>
          </button>
        )}
      </div>
    </aside>
  );
}
