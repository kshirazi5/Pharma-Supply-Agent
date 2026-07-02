"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Simple auth state stored in memory (use cookie/token store in prod) ───────
let _token: string | null = null;
export function getToken() { return _token; }
export function setToken(t: string) { _token = t; }

export async function loginUser(username: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const res = await fetch(`${API}/api/auth/token`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Login failed");
  const data = await res.json();
  setToken(data.access_token);
  return data.access_token;
}

export async function authFetch(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      ...(opts.headers ?? {}),
      Authorization: `Bearer ${_token ?? ""}`,
      "Content-Type": "application/json",
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export async function runPipeline(file: File, token: string) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/api/run-pipeline`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) throw new Error(`Pipeline error: ${res.status}`);
  return res.json();
}
