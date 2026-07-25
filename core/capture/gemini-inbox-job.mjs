#!/usr/bin/env node
/**
 * Gemini / Chat-Inbox Capture (Phase 1b)
 * Pollt /opt/ai-os/ingest/inbox/gemini/ und inbox/chats/ auf neue .md-Dateien
 * mit YAML-Frontmatter → POST /v1/chat-import
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const INBOX_ROOT = process.env.AIOS_INGEST_INBOX ?? "/opt/ai-os/ingest/inbox";
const WATCH_DIRS = [
  path.join(INBOX_ROOT, "gemini"),
  path.join(INBOX_ROOT, "chats"),
];
const STATE_PATH =
  process.env.AIOS_GEMINI_INBOX_STATE ??
  path.join(
    process.env.AIOS_MEMORY_ROOT ?? "/opt/ai-os/memory",
    "state",
    "gemini-inbox-state.json",
  );
const ORCHESTRATOR = process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";
const INTERVAL_MS = Number(process.env.CAPTURE_INTERVAL_MS ?? 60000);
const ONCE = process.argv.includes("--once");

function loadState() {
  if (!fs.existsSync(STATE_PATH)) return { files: {} };
  try {
    return JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
  } catch {
    return { files: {} };
  }
}

function saveState(state) {
  fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
  state.updated_at = new Date().toISOString();
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}

function walkMd(root) {
  const out = [];
  if (!fs.existsSync(root)) return out;
  const stack = [root];
  while (stack.length) {
    const dir = stack.pop();
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const ent of entries) {
      const full = path.join(dir, ent.name);
      if (ent.isDirectory()) stack.push(full);
      else if (ent.isFile() && ent.name.endsWith(".md")) out.push(full);
    }
  }
  return out;
}

function parseFrontmatter(text) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/m.exec(text);
  if (!m) return { meta: {}, body: text };
  const meta = {};
  for (const line of m[1].split("\n")) {
    const kv = /^(\w+):\s*(.*)$/.exec(line.trim());
    if (!kv) continue;
    let val = kv[2].trim();
    if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
    meta[kv[1]] = val;
  }
  return { meta, body: m[2] };
}

function parseMessagesFromBody(body) {
  const messages = [];
  const parts = body.split(/\*\*(Nutzer|Gemini|Assistent|User|Assistant):\*\*/i);
  if (parts.length > 1) {
    for (let i = 1; i < parts.length; i += 2) {
      const label = parts[i].toLowerCase();
      const text = (parts[i + 1] || "").trim();
      if (!text) continue;
      const role = label.includes("nutzer") || label === "user" ? "user" : "assistant";
      messages.push({ role, text });
    }
    return messages;
  }
  const trimmed = body.trim();
  if (trimmed) messages.push({ role: "user", text: trimmed });
  return messages;
}

function fileSig(filePath) {
  const st = fs.statSync(filePath);
  return `${st.mtimeMs}:${st.size}`;
}

function buildTranscript(filePath, meta, body) {
  const source = meta.source || "gemini";
  const externalId =
    meta.external_id ||
    crypto.createHash("sha256").update(filePath).digest("hex").slice(0, 16);
  const title =
    meta.title ||
    body.split("\n").find((l) => l.startsWith("# "))?.slice(2) ||
    path.basename(filePath, ".md");
  return {
    source,
    account_id: meta.account_id || "inbox",
    account_email: meta.account_email || "",
    external_id: externalId,
    session_id: meta.session_id || `ext-${source}-${externalId}`,
    url: meta.url || `file://${filePath}`,
    title,
    captured_at: meta.captured_at || new Date().toISOString(),
    source_modified_at: new Date(fs.statSync(filePath).mtimeMs).toISOString(),
    private: meta.private === "true",
    messages: parseMessagesFromBody(body),
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
  const files = state.files || {};
  let imported = 0;
  let skipped = 0;
  let errors = 0;

  for (const dir of WATCH_DIRS) {
    fs.mkdirSync(dir, { recursive: true });
    for (const filePath of walkMd(dir)) {
      const sig = fileSig(filePath);
      if (files[filePath] === sig) {
        skipped += 1;
        continue;
      }
      try {
        const raw = fs.readFileSync(filePath, "utf8");
        const { meta, body } = parseFrontmatter(raw);
        const transcript = buildTranscript(filePath, meta, body);
        if (!(transcript.messages || []).length) {
          skipped += 1;
          continue;
        }
        const resp = await postImport(transcript);
        files[filePath] = sig;
        imported += 1;
        console.log(`[gemini-inbox] ${path.basename(filePath)} → ${resp.message_count} msgs`);
      } catch (err) {
        errors += 1;
        console.error(`[gemini-inbox] ${filePath}:`, err.message || err);
      }
    }
  }

  state.files = files;
  saveState(state);
  console.log(`[gemini-inbox] imported=${imported} skipped=${skipped} errors=${errors}`);
  return { imported, skipped, errors };
}

async function main() {
  console.log(`[gemini-inbox] watching ${WATCH_DIRS.join(", ")}`);
  await pollOnce();
  if (ONCE) return;
  setInterval(() => {
    pollOnce().catch((err) => console.error("[gemini-inbox] loop:", err.message || err));
  }, INTERVAL_MS);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
