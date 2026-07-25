#!/usr/bin/env node
/**
 * Antigravity Chat Capture (Phase 1b)
 * Pollt ~/.gemini/antigravity/brain/<session>/.system_generated/logs/transcript.jsonl
 * → POST /v1/chat-import
 */
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const BRAIN_ROOT =
  process.env.ANTIGRAVITY_BRAIN_ROOT ??
  path.join(os.homedir(), ".gemini", "antigravity", "brain");
const STATE_PATH =
  process.env.AIOS_ANTIGRAVITY_STATE ??
  path.join(
    process.env.AIOS_MEMORY_ROOT ?? "/opt/ai-os/memory",
    "state",
    "antigravity-poller-state.json",
  );
const ORCHESTRATOR =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";
const INTERVAL_MS = Number(process.env.CAPTURE_INTERVAL_MS ?? 30000);
const ONCE = process.argv.includes("--once");

const USER_REQUEST_RE = /<USER_REQUEST>\s*([\s\S]*?)\s*<\/USER_REQUEST>/;
const SKIP_PREFIXES = ["Created At:", "Encountered error in step execution:"];
const ARTIFACT_FILES = ["walkthrough.md", "implementation_plan.md", "task.md"];

function loadState() {
  if (!fs.existsSync(STATE_PATH)) return { sessions: {} };
  try {
    return JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
  } catch {
    return { sessions: {} };
  }
}

function saveState(state) {
  fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
  state.updated_at = new Date().toISOString();
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}

function extractUserText(content) {
  const m = USER_REQUEST_RE.exec(content || "");
  return (m ? m[1] : content || "").trim();
}

function isMeaningfulAssistant(text) {
  const t = (text || "").trim();
  if (!t || t.length < 15) return false;
  return !SKIP_PREFIXES.some((p) => t.startsWith(p));
}

function parseTranscript(jsonlPath) {
  if (!fs.existsSync(jsonlPath)) return [];
  const messages = [];
  for (const line of fs.readFileSync(jsonlPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    let row;
    try {
      row = JSON.parse(trimmed);
    } catch {
      continue;
    }
    const ts = row.created_at;
    if (row.type === "USER_INPUT") {
      const text = extractUserText(String(row.content || ""));
      if (text) messages.push({ role: "user", text, ts });
    } else if (row.type === "PLANNER_RESPONSE") {
      const text = String(row.content || "").trim();
      if (isMeaningfulAssistant(text)) messages.push({ role: "assistant", text, ts });
    }
  }
  return messages;
}

function artifactMessages(brainDir) {
  const out = [];
  const labels = {
    "walkthrough.md": "Walkthrough (Antigravity)",
    "implementation_plan.md": "Implementierungsplan (Antigravity)",
    "task.md": "Task-Checkliste (Antigravity)",
  };
  for (const name of ARTIFACT_FILES) {
    const p = path.join(brainDir, name);
    if (!fs.existsSync(p)) continue;
    const body = fs.readFileSync(p, "utf8").trim();
    if (!body) continue;
    const mtime = new Date(fs.statSync(p).mtimeMs).toISOString();
    out.push({
      role: "assistant",
      text: `## ${labels[name] || name}\n\n${body}`,
      ts: mtime,
    });
  }
  return out;
}

function sessionTitle(messages, sessionId) {
  for (const m of messages) {
    if (m.role === "user" && m.text) {
      const t = m.text.replace(/\n/g, " ").trim();
      return t.length > 80 ? `${t.slice(0, 80)}…` : t;
    }
  }
  return `Antigravity ${sessionId.slice(0, 8)}`;
}

function fileSignature(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const st = fs.statSync(filePath);
  return { mtime: Math.floor(st.mtimeMs), size: st.size };
}

function sessionSignature(brainDir) {
  const transcript = path.join(brainDir, ".system_generated", "logs", "transcript.jsonl");
  const sig = { transcript: fileSignature(transcript) };
  for (const name of ARTIFACT_FILES) {
    sig[name] = fileSignature(path.join(brainDir, name));
  }
  return sig;
}

function discoverSessions() {
  if (!fs.existsSync(BRAIN_ROOT)) return [];
  return fs
    .readdirSync(BRAIN_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => {
      const brainDir = path.join(BRAIN_ROOT, d.name);
      const transcript = path.join(brainDir, ".system_generated", "logs", "transcript.jsonl");
      return fs.existsSync(transcript) ? [d.name, brainDir] : null;
    })
    .filter(Boolean);
}

function buildTranscript(brainDir, sessionId) {
  const transcriptPath = path.join(brainDir, ".system_generated", "logs", "transcript.jsonl");
  const messages = [...parseTranscript(transcriptPath), ...artifactMessages(brainDir)];
  const st = fs.existsSync(transcriptPath) ? fs.statSync(transcriptPath) : null;
  return {
    source: "antigravity",
    account_id: "local",
    account_email: os.userInfo().username,
    external_id: `antigravity-${sessionId}`,
    session_id: `ext-antigravity-${sessionId}`,
    url: `file://${brainDir}`,
    title: sessionTitle(messages, sessionId),
    captured_at: new Date().toISOString(),
    source_modified_at: st ? new Date(st.mtimeMs).toISOString() : "",
    private: false,
    messages,
  };
}

async function postImport(transcript) {
  const res = await fetch(`${ORCHESTRATOR}/v1/chat-import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, tenant_id: "nextchapter" }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`chat-import ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

async function pollOnce() {
  const state = loadState();
  const sessions = state.sessions || {};
  let imported = 0;
  let skipped = 0;
  let errors = 0;

  for (const [sessionId, brainDir] of discoverSessions()) {
    const sig = sessionSignature(brainDir);
    if (!sig.transcript) continue;
    const prev = sessions[sessionId]?.signature;
    if (prev && JSON.stringify(prev) === JSON.stringify(sig)) {
      skipped += 1;
      continue;
    }
    const transcript = buildTranscript(brainDir, sessionId);
    if (!(transcript.messages || []).length) {
      skipped += 1;
      continue;
    }
    try {
      const resp = await postImport(transcript);
      sessions[sessionId] = {
        signature: sig,
        imported_at: new Date().toISOString(),
        path: resp.path,
        messages: transcript.messages.length,
      };
      imported += 1;
      console.log(
        `[antigravity] import ${sessionId.slice(0, 8)} → ${resp.message_count} msgs`,
      );
    } catch (err) {
      errors += 1;
      console.error(`[antigravity] ${sessionId}:`, err.message || err);
    }
  }

  state.sessions = sessions;
  saveState(state);
  console.log(
    `[antigravity] brain=${BRAIN_ROOT} imported=${imported} skipped=${skipped} errors=${errors}`,
  );
  return { imported, skipped, errors };
}

async function main() {
  console.log(`[antigravity] watching ${BRAIN_ROOT} → ${ORCHESTRATOR}/v1/chat-import`);
  await pollOnce();
  if (ONCE) return;
  setInterval(() => {
    pollOnce().catch((err) => console.error("[antigravity] loop:", err.message || err));
  }, INTERVAL_MS);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
