"use client";

import React, { useState } from "react";
import { runEvaluation } from "@/lib/api";
import {
  Activity,
  ExternalLink,
  Play,
  CheckCircle2,
  BarChart3,
  Cpu,
  Database,
  Search,
  ShieldCheck,
  Loader2,
  AlertCircle,
} from "lucide-react";

export default function ObservabilityView() {
  const [evaluating, setEvaluating] = useState(false);
  const [evalReport, setEvalReport] = useState<any | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);

  const handleRunEvaluation = async () => {
    setEvaluating(true);
    setEvalError(null);
    try {
      const data = await runEvaluation();
      setEvalReport(data.report);
    } catch (err: any) {
      setEvalError(err.message || "Failed to run evaluation benchmark");
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-900 text-slate-100 space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <h2 className="text-xl font-bold text-white tracking-tight">
          System Observability & Automated Evaluation
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Monitor real-time Prometheus metrics, Grafana dashboards, and run Ragas benchmark evaluation pipelines.
        </p>
      </div>

      {/* Observability Links & Stack Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Grafana Card */}
        <div className="rounded-2xl border border-indigo-900/50 bg-gradient-to-br from-indigo-950/40 to-slate-950/80 p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Grafana Dashboards</h3>
                <span className="text-[11px] text-indigo-300 font-medium">Pre-provisioned metrics portal</span>
              </div>
            </div>

            <a
              href="/grafana/"
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white shadow-sm transition-colors"
            >
              <span>Open Grafana</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Visualizes FastAPI request volume, p95/p99 latency, LanceDB query times, document grader pass/fail ratios, and Tavily web fallback triggers in real time.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
            <span className="bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">Port: 3001</span>
            <span className="bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">Datasource: Prometheus</span>
            <span className="bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">Refresh: 5s</span>
          </div>
        </div>

        {/* Prometheus Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-orange-600/20 border border-orange-500/30 flex items-center justify-center text-orange-400">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Prometheus Exporter</h3>
                <span className="text-[11px] text-orange-300 font-medium">Scraping /metrics @ 5s intervals</span>
              </div>
            </div>

            <a
              href="http://localhost:8000/metrics"
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 border border-slate-700 transition-colors"
            >
              <span>Raw Metrics</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            FastAPI instrumentator automatically exposes request histograms, HTTP status counters, and custom LangGraph execution indicators on port 8000.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
            <span className="bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">Host: fastapi:8000</span>
            <span className="bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">Endpoint: /metrics</span>
          </div>
        </div>
      </div>

      {/* Automated Evaluation Section (Ragas) */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6 space-y-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Automated RAG Evaluation (Ragas)</h3>
              <p className="text-xs text-slate-400">
                Benchmarks the pipeline against industry metrics: Context Precision, Faithfulness, and Answer Relevance.
              </p>
            </div>
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={evaluating}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
          >
            {evaluating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Evaluation Benchmark...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Benchmark Test</span>
              </>
            )}
          </button>
        </div>

        {evalError && (
          <div className="flex items-center space-x-2 rounded-xl bg-red-500/10 border border-red-500/30 p-3 text-xs text-red-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{evalError}</span>
          </div>
        )}

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>Context Precision</span>
              <Search className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-white font-mono">
              {evalReport?.scores?.context_precision !== undefined
                ? (evalReport.scores.context_precision * 100).toFixed(1) + "%"
                : "--"}
            </div>
            <p className="text-[11px] text-slate-500 leading-tight">
              Measures signal-to-noise ratio in retrieved document chunks.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>Faithfulness</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white font-mono">
              {evalReport?.scores?.faithfulness !== undefined
                ? (evalReport.scores.faithfulness * 100).toFixed(1) + "%"
                : "--"}
            </div>
            <p className="text-[11px] text-slate-500 leading-tight">
              Groundedness score: verifies claims in answer against context to prevent hallucination.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>Answer Relevance</span>
              <CheckCircle2 className="w-4 h-4 text-violet-400" />
            </div>
            <div className="text-2xl font-bold text-white font-mono">
              {evalReport?.scores?.answer_relevancy !== undefined
                ? (evalReport.scores.answer_relevancy * 100).toFixed(1) + "%"
                : "--"}
            </div>
            <p className="text-[11px] text-slate-500 leading-tight">
              Verifies how directly and concisely the answer resolves the user prompt.
            </p>
          </div>
        </div>

        {/* Sample Breakdown if evaluated */}
        {evalReport?.samples && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Benchmark Sample Runs ({evalReport.samples.length})
            </h4>
            <div className="space-y-2">
              {evalReport.samples.map((s: any, i: number) => (
                <div
                  key={i}
                  className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 space-y-1.5 text-xs text-left"
                >
                  <div className="font-semibold text-indigo-300">&ldquo;{s.question}&rdquo;</div>
                  <div className="text-slate-300 leading-relaxed">{s.response}</div>
                  <div className="text-[10px] text-slate-500 flex items-center space-x-3 pt-1">
                    <span>Retrieved chunks: {s.contexts_count}</span>
                    <span>Expected target: &ldquo;{s.reference}&rdquo;</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
