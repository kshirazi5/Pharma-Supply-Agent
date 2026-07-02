"use client";

import { useState, useCallback } from "react";
import { runPipeline } from "@/lib/api";

interface Props {
  token: string;
  onResult: (result: string) => void;
}

export default function UploadPanel({ token, onResult }: Props) {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f?.name.endsWith(".csv")) setFile(f);
    else setError("Please drop a .csv file");
  }, []);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) { setFile(f); setError(""); }
  };

  const handleRun = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const res = await runPipeline(file, token);
      onResult(res.response ?? JSON.stringify(res, null, 2));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Pipeline failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl p-6 space-y-4">
      <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
        Upload Sales CSV
      </h2>

      {/* Drop zone */}
      <div
        id="drop-zone"
        onDrop={handleDrop}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer
          ${dragging ? "border-sky-400 bg-sky-500/10" : "border-slate-700 hover:border-slate-500"}`}
      >
        <input
          id="csv-upload"
          type="file"
          accept=".csv"
          onChange={handleFile}
          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
        />
        <svg className="w-10 h-10 text-slate-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        {file ? (
          <p className="text-sky-400 font-medium">{file.name}</p>
        ) : (
          <>
            <p className="text-slate-400 text-sm">Drop salesdaily.csv here</p>
            <p className="text-slate-600 text-xs mt-1">or click to browse</p>
          </>
        )}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      <button
        id="run-pipeline-btn"
        onClick={handleRun}
        disabled={!file || loading}
        className="w-full bg-gradient-to-r from-sky-500 to-violet-500 hover:from-sky-400 hover:to-violet-400
                   text-white font-semibold py-3 rounded-xl transition-all duration-200
                   shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Running Pipeline…
          </>
        ) : (
          "▶  Run AI Pipeline"
        )}
      </button>
    </div>
  );
}
