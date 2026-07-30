"use client";

import React, { useState, useRef } from "react";

interface FileUploadDropzoneProps {
  onUploadSuccess?: (result: any) => void;
}

export const FileUploadDropzone: React.FC<FileUploadDropzoneProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
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
        text: `✓ "${file.name}" erfolgreich verarbeitet (${data.text_length} Zeichen indeziert, ID: ${data.asset_id})`,
      });

      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (err: any) {
      setStatusMsg({
        type: "error",
        text: `❌ Upload-Fehler: ${err.message}`,
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
    <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-slate-100 mb-2 flex items-center gap-2">
        <span>📄</span> Dokument-Upload & Ingestion
      </h3>
      <p className="text-xs text-slate-400 mb-4">
        PDF, Markdown, TXT oder CSV hochladen — wird automatisch im Memory indeziert und als OrgKnowledgeAsset gespeichert.
      </p>

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          dragActive
            ? "border-emerald-500 bg-emerald-950/20"
            : "border-slate-700 hover:border-slate-500 bg-slate-950/40"
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
          <div className="flex items-center justify-center gap-2 text-slate-300">
            <span className="animate-spin">⏳</span>
            <span>Verarbeite Dokument...</span>
          </div>
        ) : (
          <div>
            <div className="text-3xl mb-2">📥</div>
            <div className="text-sm font-medium text-slate-200">
              Datei hierher ziehen oder <span className="text-emerald-400 underline">durchsuchen</span>
            </div>
            <div className="text-xs text-slate-500 mt-1">PDF, MD, TXT, CSV (max. 50 MB)</div>
          </div>
        )}
      </div>

      {statusMsg && (
        <div
          className={`mt-4 p-3 rounded-lg text-xs font-mono ${
            statusMsg.type === "success"
              ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/60"
              : "bg-rose-950/60 text-rose-300 border border-rose-800/60"
          }`}
        >
          {statusMsg.text}
        </div>
      )}
    </div>
  );
};
