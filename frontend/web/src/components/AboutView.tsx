"use client";

import React from "react";
import {
  Layers,
  Database,
  Search,
  CheckCircle,
  FileCheck,
  Globe,
  Mail,
  Cpu,
  Code2,
  ExternalLink,
} from "lucide-react";

export default function AboutView() {
  const steps = [
    {
      title: "1. Question Router",
      desc: "Structured LLM router analyzes the user prompt to decide whether to query local knowledge base or initiate web search.",
      icon: <Search className="w-4 h-4 text-indigo-400" />,
    },
    {
      title: "2. LanceDB Retrieval",
      desc: "Queries high-performance Arrow vector store, filtering by authenticated user_id with sub-millisecond retrieval.",
      icon: <Database className="w-4 h-4 text-violet-400" />,
    },
    {
      title: "3. Document Relevance Grader",
      desc: "Evaluates each retrieved chunk against the query. Discards irrelevant noise and flags web search fallback if context is insufficient.",
      icon: <FileCheck className="w-4 h-4 text-emerald-400" />,
    },
    {
      title: "4. Tavily Web Fallback",
      desc: "If document context is inadequate or external real-time data is required, queries Tavily Search API to supplement context.",
      icon: <Globe className="w-4 h-4 text-amber-400" />,
    },
    {
      title: "5. Grounded Generation",
      desc: "Synthesizes final answer strictly grounded in the filtered context, copying entities, dates, and numbers accurately.",
      icon: <Cpu className="w-4 h-4 text-indigo-400" />,
    },
    {
      title: "6. Hallucination Grader",
      desc: "Evaluates whether the generation is fully supported by the facts. If hallucinated claims are detected, retries generation.",
      icon: <CheckCircle className="w-4 h-4 text-emerald-400" />,
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-900 text-slate-100 space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <h2 className="text-xl font-bold text-white tracking-tight">
          System Architecture & Agentic Workflow
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Based on the state-of-the-art Corrective RAG and Self-Reflective LangGraph paradigm.
        </p>
      </div>

      {/* Pipeline Steps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 space-y-2.5 shadow-sm hover:border-slate-700 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center">
                {step.icon}
              </div>
              <h3 className="text-xs font-bold text-white">{step.title}</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
          </div>
        ))}
      </div>

      {/* Tech Stack Specs */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5 space-y-3">
        <h3 className="text-sm font-bold text-white">Full Stack Technologies</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-300">
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
            <span className="font-semibold text-indigo-400 block mb-0.5">Frontend</span>
            Next.js 15 + Tailwind CSS + Lucide
          </div>
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
            <span className="font-semibold text-violet-400 block mb-0.5">Backend</span>
            FastAPI + LangGraph + LangChain
          </div>
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
            <span className="font-semibold text-emerald-400 block mb-0.5">Vector Store</span>
            LanceDB (Embedded Apache Arrow)
          </div>
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
            <span className="font-semibold text-amber-400 block mb-0.5">Observability</span>
            Prometheus + Grafana + Ragas
          </div>
        </div>
      </div>

      {/* Author & Connect */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5 space-y-4">
        <h3 className="text-sm font-bold text-white">Project & Author</h3>
        <p className="text-xs text-slate-400 leading-relaxed max-w-xl">
          Designed and implemented by <strong>Amrit Bhaganagare</strong>. Built for high-reliability technical document QA, with zero hallucination tolerance and full containerized observability.
        </p>
        <div className="flex flex-wrap items-center gap-3 pt-1">
          <a
            href="mailto:08amrit@gmail.com"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 transition-colors"
          >
            <Mail className="w-3.5 h-3.5 text-indigo-400" />
            <span>08amrit@gmail.com</span>
          </a>
          <a
            href="https://www.linkedin.com/in/amrit-bhaganagare/"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5 text-blue-400" />
            <span>LinkedIn Profile</span>
          </a>
          <a
            href="https://github.com/Amrit-B/rag-app"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 transition-colors"
          >
            <Code2 className="w-3.5 h-3.5 text-white" />
            <span>GitHub Repository</span>
          </a>
        </div>
      </div>
    </div>
  );
}
