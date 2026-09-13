"use client";

import React, { useState, useRef } from "react";
import { DocumentRecord, uploadDocument, pollUploadStatus, deleteDocument, resetKnowledgeBase } from "@/lib/api";
import {
  UploadCloud,
  FileText,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  HardDrive,
  RefreshCw,
  Loader2,
} from "lucide-react";

interface DocumentsViewProps {
  documents: DocumentRecord[];
  onRefresh: () => void;
  username: string | null;
  onOpenAuth: () => void;
}

export default function DocumentsView({
  documents,
  onRefresh,
  username,
  onOpenAuth,
}: DocumentsViewProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatusText, setUploadStatusText] = useState<string | null>(null);
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);
  const totalSizeBytes = documents.reduce((acc, d) => acc + (d.file_size_bytes || 0), 0);
  const totalSizeMB = (totalSizeBytes / (1024 * 1024)).toFixed(2);

  const handleFileUpload = async (file: File) => {
    if (!username) {
      onOpenAuth();
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF documents are supported.");
      return;
    }

    setError(null);
    setUploading(true);
    setUploadStatusText("Uploading PDF to server...");

    try {
      const { job_id } = await uploadDocument(file);
      setUploadStatusText("Cleaning noise & generating technical chunks...");

      // Poll until finished
      const interval = setInterval(async () => {
        try {
          const res = await pollUploadStatus(job_id);
          if (res.status === "completed") {
            clearInterval(interval);
            setUploading(false);
            setUploadStatusText(null);
            onRefresh();
          } else if (res.status === "failed") {
            clearInterval(interval);
            setUploading(false);
            setUploadStatusText(null);
            setError(res.error || "Ingestion failed.");
            onRefresh();
          }
        } catch {
          // keep polling
        }
      }, 1200);
    } catch (err: any) {
      setUploading(false);
      setUploadStatusText(null);
      setError(err.message || "Upload failed");
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId);
      onRefresh();
    } catch (err: any) {
      setError(err.message || "Failed to delete document");
    }
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await resetKnowledgeBase();
      setResetModalOpen(false);
      onRefresh();
    } catch (err: any) {
      setError(err.message || "Failed to reset knowledge base");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-900 text-slate-100 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Knowledge Base & Document Store
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ingest PDFs with automatic header/footer noise removal and technical recursive chunking into LanceDB.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setResetModalOpen(true)}
            disabled={documents.length === 0}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-xs font-medium text-red-300 transition-colors disabled:opacity-40"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Reset Knowledge Base</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center space-x-2 rounded-xl bg-red-500/10 border border-red-500/30 p-3.5 text-xs text-red-400">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex items-center space-x-3.5 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{documents.length}</div>
            <div className="text-xs text-slate-400 font-medium">Uploaded Documents</div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex items-center space-x-3.5 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{totalChunks}</div>
            <div className="text-xs text-slate-400 font-medium">Vector Chunks Indexed</div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex items-center space-x-3.5 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{totalSizeMB} MB</div>
            <div className="text-xs text-slate-400 font-medium">Storage Consumed</div>
          </div>
        </div>
      </div>

      {/* Upload Dropzone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          uploading
            ? "border-indigo-500 bg-indigo-950/20"
            : "border-slate-700/80 bg-slate-950/40 hover:border-indigo-500/60 hover:bg-slate-900/60"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileUpload(file);
          }}
        />

        <div className="flex flex-col items-center space-y-3 max-w-sm mx-auto">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            {uploading ? (
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            ) : (
              <UploadCloud className="w-6 h-6" />
            )}
          </div>

          <div>
            <div className="text-sm font-semibold text-white">
              {uploading ? uploadStatusText : "Click or drag PDF to upload"}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Supports technical PDFs up to 200MB. Cleaned and indexed automatically into LanceDB.
            </p>
          </div>
        </div>
      </div>

      {/* Document List Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Indexed Documents</h3>
          <span className="text-xs text-slate-400">{documents.length} files</span>
        </div>

        {documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 italic">
            No documents in your knowledge base yet. Upload a PDF above to get started!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3">Document</th>
                  <th className="px-5 py-3">Chunks</th>
                  <th className="px-5 py-3">File Size</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => (
                  <tr key={doc.doc_id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-5 py-3.5 flex items-center space-x-2.5 font-medium text-slate-200">
                      <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                      <span className="truncate max-w-xs sm:max-w-md">{doc.filename}</span>
                    </td>
                    <td className="px-5 py-3.5 text-slate-300 font-mono">
                      {doc.chunk_count} chunks
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {(doc.file_size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
                          doc.status === "completed"
                            ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
                            : doc.status === "processing"
                            ? "bg-amber-950/40 border-amber-800 text-amber-300"
                            : "bg-red-950/40 border-red-800 text-red-300"
                        }`}
                      >
                        {doc.status === "completed" ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <Clock className="w-3 h-3" />
                        )}
                        <span className="capitalize">{doc.status}</span>
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => handleDelete(doc.doc_id)}
                        className="text-slate-400 hover:text-red-400 p-1 rounded transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reset Confirmation Modal */}
      {resetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="relative w-full max-w-sm rounded-2xl border border-red-500/30 bg-slate-900 p-6 shadow-2xl text-slate-100 space-y-4">
            <div className="w-10 h-10 rounded-xl bg-red-600/20 border border-red-500/30 flex items-center justify-center text-red-400">
              <AlertTriangle className="w-5 h-5" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">Reset Knowledge Base?</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                This will permanently delete all your uploaded PDFs, vector chunk partitions, and indexed records. This action cannot be undone.
              </p>
            </div>

            <div className="flex space-x-3 pt-2">
              <button
                onClick={() => setResetModalOpen(false)}
                className="flex-1 rounded-lg border border-slate-700 bg-slate-800 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleReset}
                disabled={isResetting}
                className="flex-1 rounded-lg bg-red-600 hover:bg-red-500 py-2 text-xs font-medium text-white shadow-md shadow-red-600/30 transition-all disabled:opacity-50"
              >
                {isResetting ? "Resetting..." : "Confirm Reset"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
