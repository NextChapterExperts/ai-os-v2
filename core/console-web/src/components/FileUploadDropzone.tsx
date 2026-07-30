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
    <div className="w-full border border-[var(--line)] bg-[color-mix(in_oklab,white_65%,transparent)] rounded-2xl p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="section-title text-base font-bold text-[var(--ink)] flex items-center gap-2 m-0">
            <span className="text-[var(--signal)]">📄</span> Dokument-Upload & Ingestion Pipeline
          </h3>
          <p className="text-xs muted mt-1 m-0">
            Automatische Text- & PDF-Extraktion, SQLite FTS-Indizierung und OrgKnowledgeAsset-Commit in den Knowledge Graph.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {["PDF", "MD", "TXT", "CSV"].map((ext) => (
            <span key={ext} className="badge" data-variant="curated">
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
            ? "border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_12%,white)] scale-[1.01]"
            : "border-[var(--line)] hover:border-[var(--signal)] bg-white hover:bg-[color-mix(in_oklab,white_90%,transparent)]"
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
          <div className="flex flex-col items-center justify-center gap-2 py-3 text-[var(--ink)]">
            <span className="animate-spin text-2xl">⏳</span>
            <span className="text-sm font-medium">Verarbeite & indiziere Dokument...</span>
            <span className="text-xs mono muted">FTS Indexing & Knowledge Graph Commit</span>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-3xl">📥</div>
            <div className="text-sm font-semibold text-[var(--ink)]">
              Datei hierher ziehen oder <span className="text-[var(--signal)] underline">durchsuchen</span>
            </div>
            <div className="text-xs muted">PDF, Markdown, Plaintext, CSV (automatische Deduplizierung via SHA256)</div>
          </div>
        )}
      </div>

      {statusMsg && (
        <div
          className={`mt-4 p-4 rounded-xl text-xs mono transition-all border ${
            statusMsg.type === "success"
              ? "bg-[color-mix(in_oklab,var(--signal)_10%,white)] text-[var(--signal)] border-[var(--signal)]"
              : "bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] border-[var(--danger)]"
          }`}
        >
          <div>{statusMsg.text}</div>
          {statusMsg.details && (
            <div className="mt-2 pt-2 border-t border-[var(--line)] flex flex-wrap items-center justify-between text-[11px]">
              <span>Path: {statusMsg.details.path}</span>
              <span>Hash: {statusMsg.details.hash?.slice(0, 16)}...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
