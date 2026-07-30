"use client";

import React, { useState, useRef } from "react";

interface FileUploadDropzoneProps {
  onUploadSuccess?: (result: any) => void;
}

export const FileUploadDropzone: React.FC<FileUploadDropzoneProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string; details?: any } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    setUploading(true);
    setStatusMsg(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("tenant_id", "nextchapter");

    try {
      const res = await fetch("/api/ingest/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.detail || data.error || "Upload fehlgeschlagen");
      }

      setStatusMsg({
        type: "success",
        text: `✓ "${file.name}" verarbeitet (${data.text_length} Zeichen, Asset: ${data.asset_id})`,
        details: data,
      });

      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (err: any) {
      setStatusMsg({
        type: "error",
        text: `❌ Ingestion-Fehler: ${err.message}`,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="w-full bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span className="text-emerald-400">📄</span> Dokument-Upload & Ingestion Pipeline
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Automatische Text- & PDF-Extraktion, SQLite FTS-Indizierung und OrgKnowledgeAsset-Commit in den Knowledge Graph.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {["PDF", "MD", "TXT", "CSV"].map((ext) => (
            <span
              key={ext}
              className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700"
            >
              {ext}
            </span>
          ))}
        </div>
      </div>

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          dragActive
            ? "border-emerald-400 bg-emerald-950/30 scale-[1.01]"
            : "border-slate-700/80 hover:border-emerald-500/60 bg-slate-950/60 hover:bg-slate-950/80"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.md,.markdown,.txt,.csv,.json"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        {uploading ? (
          <div className="flex flex-col items-center justify-center gap-2 py-3 text-slate-200">
            <span className="animate-spin text-2xl">⏳</span>
            <span className="text-sm font-medium">Verarbeite & indiziere Dokument...</span>
            <span className="text-xs text-slate-500 font-mono">FTS Indexing & Knowledge Graph Commit</span>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-3xl">📥</div>
            <div className="text-sm font-medium text-slate-200">
              Datei hierher ziehen oder <span className="text-emerald-400 underline font-semibold">durchsuchen</span>
            </div>
            <div className="text-xs text-slate-500">PDF, Markdown, Plaintext, CSV (automatische Deduplizierung via SHA256)</div>
          </div>
        )}
      </div>

      {statusMsg && (
        <div
          className={`mt-4 p-4 rounded-xl text-xs font-mono transition-all ${
            statusMsg.type === "success"
              ? "bg-emerald-950/70 text-emerald-300 border border-emerald-800/80"
              : "bg-rose-950/70 text-rose-300 border border-rose-800/80"
          }`}
        >
          <div>{statusMsg.text}</div>
          {statusMsg.details && (
            <div className="mt-2 pt-2 border-t border-emerald-800/50 flex flex-wrap items-center justify-between text-[11px] text-emerald-400/90">
              <span>Path: {statusMsg.details.path}</span>
              <span>Hash: {statusMsg.details.hash?.slice(0, 16)}...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
