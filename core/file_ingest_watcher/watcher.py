#!/usr/bin/env python3
"""File-Ingest-Watcher (MVP / Horizont 1 - Bruecke, siehe docs/adr/0002).

Scannt die konfigurierten WATCH_ROOTS (Standard: Projekte/active), erkennt
neue/geaenderte/geloeschte Dateien per Hash-Diff, extrahiert Text, chunked
und embedded ihn und schreibt ihn in die Qdrant-Collection "raw-files".

Diese Collection ist bewusst getrennt vom kuratierten Company-Brain (L1
"content"): Rohdateien sind ungeprueft und sollen in der spaeteren Unified
Search klar als "Rohdatei" markiert werden, nicht mit freigegebenem Wissen
vermischt werden.

Optional wird vor jedem Scan ein Git-Snapshot des Projekte-Repos erzeugt,
damit Fragen wie "wie sah das vor 3 Monaten aus" ueber `git log` beantwortet
werden koennen.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import frontmatter
from fastembed import TextEmbedding
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("file-ingest-watcher")

WATCH_ROOTS = [
    Path(p).expanduser()
    for p in os.environ.get(
        "WATCH_ROOTS", str(Path.home() / "Projekte" / "active")
    ).split(":")
    if p.strip()
]
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "raw-files")
EMBED_MODEL = os.environ.get(
    "EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
SCAN_INTERVAL_SEC = int(os.environ.get("SCAN_INTERVAL_SEC", "300"))
STATE_DB = Path(
    os.environ.get("STATE_DB", "/opt/ai-os/ingest/file_watcher_state.db")
).expanduser()
MAX_FILE_SIZE_MB = float(os.environ.get("MAX_FILE_SIZE_MB", "25"))
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))

GIT_SNAPSHOT_ENABLED = os.environ.get("GIT_SNAPSHOT_ENABLED", "true").lower() == "true"
GIT_SNAPSHOT_REPO = Path(
    os.environ.get("GIT_SNAPSHOT_REPO", str(Path.home() / "Projekte"))
).expanduser()

TEXT_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".sh", ".csv", ".html", ".css", ".sql",
    ".mjs", ".cjs", ".toml", ".ini", ".env.example",
}
PDF_EXTENSIONS = {".pdf"}

IGNORE_DIR_NAMES = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
    ".next", ".vite-temp", ".obsidian", ".cache", ".DS_Store",
}

# Verzeichnisnamen, die auf Backup-/Archiv-Kopien hindeuten (case-insensitive
# Teilstring-Match) - werden uebersprungen, um Duplikate in der Suche zu
# vermeiden (z.B. "Archiv", "Archiv_Backups", "_backup_20260627", "_archiv").
IGNORE_DIR_SUBSTRINGS = {"archiv", "backup"}


def _is_ignored_dir(name: str) -> bool:
    if name in IGNORE_DIR_NAMES or name.startswith("."):
        return True
    lowered = name.lower()
    return any(sub in lowered for sub in IGNORE_DIR_SUBSTRINGS)


@dataclass
class FileState:
    sha256: str
    mtime: float
    size: int
    chunk_count: int


def iter_candidate_files():
    for root in WATCH_ROOTS:
        if not root.exists():
            log.warning("WATCH_ROOT existiert nicht: %s", root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not _is_ignored_dir(d)]
            for name in filenames:
                p = Path(dirpath) / name
                if p.suffix.lower() in TEXT_EXTENSIONS | PDF_EXTENSIONS:
                    yield p


def project_slug_for(path: Path) -> str:
    for root in WATCH_ROOTS:
        try:
            rel = path.relative_to(root)
            return f"{root.name}/{rel.parts[0]}" if rel.parts else root.name
        except ValueError:
            continue
    return path.parent.name


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text(path: Path) -> tuple[str, dict]:
    """Liefert (text, extra_metadata)."""
    suffix = path.suffix.lower()
    if suffix in PDF_EXTENSIONS:
        try:
            reader = PdfReader(str(path))
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
            return text, {}
        except Exception as exc:
            log.warning("PDF-Extraktion fehlgeschlagen fuer %s: %s", path, exc)
            return "", {}

    raw = path.read_text(encoding="utf-8", errors="ignore")
    if suffix in {".md", ".markdown"}:
        try:
            post = frontmatter.loads(raw)
            meta = {
                k: v for k, v in post.metadata.items()
                if isinstance(v, (str, int, float, bool))
            }
            return post.content, meta
        except Exception:
            return raw, {}
    return raw, {}


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            break_idx = text.rfind(" ", start, end)
            if break_idx > start + (size // 2):
                end = break_idx
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def point_id_for(source_path: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"raw-file://{source_path}#{chunk_index}"))


def init_state_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            mtime REAL NOT NULL,
            size INTEGER NOT NULL,
            chunk_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def load_state(conn: sqlite3.Connection) -> dict[str, FileState]:
    rows = conn.execute("SELECT path, sha256, mtime, size, chunk_count FROM files")
    return {
        path: FileState(sha256=sha256, mtime=mtime, size=size, chunk_count=chunk_count)
        for path, sha256, mtime, size, chunk_count in rows
    }


def ensure_collection(client: QdrantClient, dim: int) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if QDRANT_COLLECTION not in existing:
        log.info("Erstelle Qdrant-Collection '%s' (dim=%d)", QDRANT_COLLECTION, dim)
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )


def delete_points_for_path(client: QdrantClient, source_path: str) -> None:
    client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(
                must=[qm.FieldCondition(key="source_path", match=qm.MatchValue(value=source_path))]
            )
        ),
    )


def git_snapshot() -> None:
    if not GIT_SNAPSHOT_ENABLED or not GIT_SNAPSHOT_REPO.exists():
        return
    try:
        subprocess.run(
            ["git", "-C", str(GIT_SNAPSHOT_REPO), "add", "-A"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        status = subprocess.run(
            ["git", "-C", str(GIT_SNAPSHOT_REPO), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not status.stdout.strip():
            return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(
            ["git", "-C", str(GIT_SNAPSHOT_REPO), "commit", "-q", "-m", f"auto-snapshot: {ts}"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        log.info("Git-Snapshot erstellt (%s)", ts)
    except subprocess.CalledProcessError as exc:
        log.warning("Git-Snapshot fehlgeschlagen: %s", exc.stderr.decode(errors="ignore") if exc.stderr else exc)
    except subprocess.TimeoutExpired:
        log.warning("Git-Snapshot Zeitüberschreitung (Timeout nach 30s)")
    except Exception as exc:
        log.warning("Git-Snapshot unerwarteter Fehler: %s", exc)


def run_scan(client: QdrantClient, embedder: TextEmbedding, conn: sqlite3.Connection) -> None:
    git_snapshot()

    state = load_state(conn)
    seen_paths: set[str] = set()
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    new_or_changed = 0
    unchanged = 0
    skipped = 0

    for path in iter_candidate_files():
        try:
            stat = path.stat()
        except OSError:
            continue
        key = str(path)
        seen_paths.add(key)

        if stat.st_size > max_bytes:
            skipped += 1
            continue

        prev = state.get(key)
        if prev and prev.mtime == stat.st_mtime and prev.size == stat.st_size:
            unchanged += 1
            continue

        try:
            digest = sha256_of(path)
        except OSError as exc:
            log.warning("Konnte Datei nicht lesen: %s (%s)", path, exc)
            continue

        if prev and prev.sha256 == digest:
            conn.execute(
                "UPDATE files SET mtime=?, size=? WHERE path=?",
                (stat.st_mtime, stat.st_size, key),
            )
            conn.commit()
            unchanged += 1
            continue

        text, extra_meta = extract_text(path)
        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        if not chunks:
            skipped += 1
            continue

        if prev:
            delete_points_for_path(client, key)

        vectors = list(embedder.embed(chunks))
        slug = project_slug_for(path)
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            payload = {
                "source": "raw-files",
                "source_path": key,
                "project_slug": slug,
                "file_name": path.name,
                "ext": path.suffix.lower(),
                "chunk_index": i,
                "chunk_count": len(chunks),
                "text": chunk,
                "sha256": digest,
                "mtime": stat.st_mtime,
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            payload.update(extra_meta)
            points.append(
                qm.PointStruct(id=point_id_for(key, i), vector=vector.tolist(), payload=payload)
            )
        client.upsert(collection_name=QDRANT_COLLECTION, points=points)

        conn.execute(
            "INSERT OR REPLACE INTO files (path, sha256, mtime, size, chunk_count, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (key, digest, stat.st_mtime, stat.st_size, len(chunks), time.strftime("%Y-%m-%dT%H:%M:%S")),
        )
        conn.commit()
        new_or_changed += 1
        log.info("Indexiert: %s (%d Chunks)", key, len(chunks))

    deleted_paths = set(state.keys()) - seen_paths
    for key in deleted_paths:
        delete_points_for_path(client, key)
        conn.execute("DELETE FROM files WHERE path=?", (key,))
    if deleted_paths:
        conn.commit()

    log.info(
        "Scan fertig: %d neu/geaendert, %d unveraendert, %d uebersprungen, %d geloescht",
        new_or_changed, unchanged, skipped, len(deleted_paths),
    )


def main() -> None:
    once = "--once" in sys.argv

    log.info("Watch-Roots: %s", ", ".join(str(p) for p in WATCH_ROOTS))
    log.info("Qdrant: %s / Collection: %s", QDRANT_URL, QDRANT_COLLECTION)
    log.info("Embedding-Modell: %s", EMBED_MODEL)

    embedder = TextEmbedding(model_name=EMBED_MODEL)
    dim = len(list(embedder.embed(["dimensionscheck"]))[0])

    client = QdrantClient(url=QDRANT_URL)
    ensure_collection(client, dim)
    conn = init_state_db(STATE_DB)

    while True:
        try:
            run_scan(client, embedder, conn)
        except Exception:
            log.exception("Scan-Durchlauf fehlgeschlagen")
        if once:
            break
        time.sleep(SCAN_INTERVAL_SEC)


if __name__ == "__main__":
    main()
