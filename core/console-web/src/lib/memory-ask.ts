import {
  DEFAULT_MEMORY_PROJECT,
  getMemoryDb,
  searchMemory,
  type MemoryChunk,
} from "./memory";

const STOP = new Set([
  "was",
  "haben",
  "wir",
  "heute",
  "gemacht",
  "ist",
  "sind",
  "der",
  "die",
  "das",
  "und",
  "oder",
  "ein",
  "eine",
  "mit",
  "von",
  "zu",
  "im",
  "in",
  "am",
  "an",
  "auf",
  "für",
  "wie",
  "wo",
  "wann",
  "wer",
  "welche",
  "welcher",
  "welches",
  "bitte",
  "mal",
  "mir",
  "mich",
  "uns",
  "euch",
  "ihr",
  "ich",
  "du",
  "er",
  "sie",
  "es",
  "denn",
  "doch",
  "noch",
  "schon",
  "auch",
  "nur",
  "sehr",
  "ganz",
  "kann",
  "können",
  "soll",
  "sollte",
  "will",
  "wollte",
  "über",
  "unter",
  "zwischen",
  "gibt",
  "dazu",
  "hier",
  "dort",
  "alles",
  "alle",
  "etwas",
  "nichts",
  "zusammenfassung",
  "zusammenfassen",
  "überblick",
  "zeig",
  "zeige",
  "erzähl",
  "erkläre",
  "sag",
  "sage",
  "detail",
  "detailliert",
  "ausführlich",
  "genau",
]);

function berlinDayBounds(now = new Date()): {
  startIso: string;
  endIso: string;
  label: string;
} {
  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Berlin",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const day = fmt.format(now);
  const startLocal = new Date(`${day}T00:00:00`);
  const offsetMin = berlinOffsetMinutes(startLocal);
  const startUtc = new Date(startLocal.getTime() - offsetMin * 60_000);
  const endUtc = new Date(startUtc.getTime() + 24 * 60 * 60 * 1000);
  return {
    startIso: startUtc.toISOString(),
    endIso: endUtc.toISOString(),
    label: day,
  };
}

function berlinOffsetMinutes(date: Date): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Europe/Berlin",
    timeZoneName: "shortOffset",
  }).formatToParts(date);
  const tz = parts.find((p) => p.type === "timeZoneName")?.value ?? "GMT+1";
  const m = tz.match(/GMT([+-])(\d{1,2})(?::?(\d{2}))?/i);
  if (!m) return 60;
  const sign = m[1] === "-" ? -1 : 1;
  const h = Number(m[2]);
  const min = Number(m[3] ?? "0");
  return sign * (h * 60 + min);
}

export function isNarrativeQuestion(q: string): boolean {
  const s = q.trim().toLowerCase();
  if (s.includes("?")) return true;
  return /\b(was|wie|warum|wieso|weshalb|erzähl|zusammenfass|überblick|heute|bisher|gemacht|passiert|status|stand)\b/i.test(
    s,
  );
}

export function wantsDetail(q: string): boolean {
  return /\b(detail|detailliert|ausführlich|genau|mehr\s+dazu|tief|bitte\s+mehr)\b/i.test(
    q,
  );
}

export function chunksForToday(
  limit = 80,
  projectId: string | null = DEFAULT_MEMORY_PROJECT,
): MemoryChunk[] {
  const { startIso, endIso } = berlinDayBounds();
  const db = getMemoryDb();
  if (projectId) {
    return db
      .prepare(
        `SELECT id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at
         FROM chunks
         WHERE project_id = ? AND ingested_at >= ? AND ingested_at < ?
         ORDER BY ingested_at ASC
         LIMIT ?`,
      )
      .all(projectId, startIso, endIso, limit) as MemoryChunk[];
  }
  return db
    .prepare(
      `SELECT id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at
       FROM chunks
       WHERE ingested_at >= ? AND ingested_at < ?
       ORDER BY ingested_at ASC
       LIMIT ?`,
    )
    .all(startIso, endIso, limit) as MemoryChunk[];
}

function keywordTerms(q: string): string[] {
  return q
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s_-]/gu, " ")
    .split(/\s+/)
    .filter((t) => t.length >= 3 && !STOP.has(t))
    .slice(0, 8);
}

export function retrieveForQuestion(
  question: string,
  limit = 40,
  projectId: string | null = DEFAULT_MEMORY_PROJECT,
): {
  mode: "today" | "hybrid" | "fts";
  chunks: MemoryChunk[];
  dayLabel: string;
  detail: boolean;
} {
  const q = question.trim();
  const detail = wantsDetail(q);
  const { label: dayLabel } = berlinDayBounds();
  const wantsToday = /\bheute\b/i.test(q) || /\bwas\s+haben\s+wir\b/i.test(q);

  if (wantsToday) {
    const today = chunksForToday(detail ? 100 : 60, projectId);
    if (today.length) {
      const users = today.filter((c) => c.role === "user");
      if (!detail) {
        return {
          mode: "today",
          chunks: users.slice(0, Math.min(limit, 30)),
          dayLabel,
          detail,
        };
      }
      const assistants = today.filter((c) => c.role === "assistant").slice(-12);
      const merged = [...users, ...assistants].slice(0, limit);
      return {
        mode: "today",
        chunks: merged.length ? merged : today.slice(0, limit),
        dayLabel,
        detail,
      };
    }
  }

  const terms = keywordTerms(q);
  const ftsHits = terms.length
    ? searchMemory(terms.join(" "), limit, projectId)
    : searchMemory(q, Math.min(limit, 20), projectId);

  if (ftsHits.length >= 3) {
    return { mode: "fts", chunks: ftsHits, dayLabel, detail };
  }

  const today = chunksForToday(40, projectId);
  const db = getMemoryDb();
  const recent = (
    projectId
      ? db
          .prepare(
            `SELECT id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at
             FROM chunks WHERE project_id = ? AND role = 'user'
             ORDER BY ingested_at DESC LIMIT 25`,
          )
          .all(projectId)
      : db
          .prepare(
            `SELECT id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at
             FROM chunks WHERE role = 'user'
             ORDER BY ingested_at DESC LIMIT 25`,
          )
          .all()
  ) as MemoryChunk[];

  const byId = new Map<string, MemoryChunk>();
  for (const c of [...ftsHits, ...today, ...recent]) byId.set(c.id, c);
  return {
    mode: "hybrid",
    chunks: [...byId.values()].slice(0, limit),
    dayLabel,
    detail,
  };
}

function buildContext(
  chunks: MemoryChunk[],
  detail: boolean,
  maxChars = 8000,
): string {
  const parts: string[] = [];
  let used = 0;
  const cap = detail ? maxChars : Math.min(maxChars, 4500);
  for (const c of chunks) {
    const body =
      c.role === "user"
        ? c.body.slice(0, detail ? 900 : 220)
        : c.body.slice(0, detail ? 500 : 120);
    const block = `[${c.role}] ${body}`;
    if (used + block.length > cap) break;
    parts.push(block);
    used += block.length;
  }
  return parts.join("\n---\n");
}

function orchestratorUrl() {
  return process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";
}

export async function summarizeMemory(
  question: string,
  chunks: MemoryChunk[],
  detail: boolean,
): Promise<{ answer: string; model: string }> {
  if (!chunks.length) {
    return {
      answer:
        "Im Gedächtnis dieses Projekts liegen dazu noch keine Einträge.",
      model: "none",
    };
  }

  const context = buildContext(chunks, detail);

  const system = detail
    ? `Du bist das AI-OS Company Brain. Antworte auf Deutsch, nur aus dem Kontext. Erfinde nichts.
Detaillierte Antwort: konkrete Schritte, Dateien, Entscheidungen. Max. 10 Bulletpoints + kurzes Fazit.`
    : `Du bist das AI-OS Company Brain. Antworte auf Deutsch, nur aus dem Kontext. Erfinde nichts.
KURZ und HOCHFLUG: maximal 5 Bulletpoints, jeweils eine Zeile, nur die großen Themen.
Keine Dateipfade, keine technischen Kleinschritte, kein langes Fazit (max. 1 Satz).
Details nur wenn der Nutzer danach fragt.`;

  const res = await fetch(`${orchestratorUrl()}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: [
        { role: "system", content: system },
        {
          role: "user",
          content: `Frage: ${question}\n\nGedächtnis-Kontext:\n${context}`,
        },
      ],
      tenant_id: "nextchapter",
      produced_by: "console-memory-ask",
      max_tokens: detail ? 900 : 280,
      temperature: 0.2,
      persist: true,
    }),
    signal: AbortSignal.timeout(120_000),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Memory Gateway ${res.status}: ${text.slice(0, 200)}`);
  }

  const data = (await res.json()) as { content?: string; model?: string };
  const answer = data.content?.trim() || "Keine Antwort vom Modell.";
  return { answer, model: data.model ?? "memory-gateway" };
}

export async function askMemory(
  question: string,
  projectId: string | null = DEFAULT_MEMORY_PROJECT,
) {
  const retrieved = retrieveForQuestion(question, 40, projectId);
  const { answer, model } = await summarizeMemory(
    question,
    retrieved.chunks,
    retrieved.detail,
  );
  const sourceLimit = retrieved.detail ? 25 : 8;
  return {
    question,
    mode: retrieved.mode,
    dayLabel: retrieved.dayLabel,
    detail: retrieved.detail,
    projectId: projectId ?? "all",
    answer,
    model,
    sources: retrieved.chunks.slice(0, sourceLimit).map((c) => ({
      id: c.id,
      role: c.role,
      title: c.title || c.body.slice(0, 80),
      snippet: c.body.slice(0, retrieved.detail ? 220 : 120) + (c.body.length > 120 ? "…" : ""),
      chat_id: c.chat_id,
      source: c.source,
      project_id: c.project_id,
      ingested_at: c.ingested_at,
    })),
    sourceCount: retrieved.chunks.length,
  };
}
