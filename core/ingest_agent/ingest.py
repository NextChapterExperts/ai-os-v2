#!/usr/bin/env python3
"""Ingest-Agent (Phase 2 MVP) — Seed-Markdown + brain.json -> DP-Commit.

Liest die kuratierten Company-Brain-Seed-Quellen und committet sie als
typisierte org:*-DataProducts ueber POST /v1/dataproduct/commit (siehe
core/orchestrator/dp_service.py). Kein Direktzugriff auf Postgres/Qdrant fuer
Knoten/Kanten — nur ueber den DP-Service (P15). Fuer OrgKnowledgeAssets mit
`published: true` chunked/embedded dieser Agent zusaetzlich in die Qdrant-
Collection `content` (Ingest-Worker-Rolle, siehe docs/03-DATENPRODUKTE.md
"Speicher-Regeln nach storage_target").

Quellen (alle unter customers/nextchapter/knowledge/seed/, siehe
docs/09-COMPANY-BRAIN.md §3.3 / §7):
  00-organization.md   -> 1x OrgOrganization  (Frontmatter)
  01-offerings.md      -> Nx OrgOffering      (Fenced-YAML-Bloecke)
  02-people.md         -> Nx OrgPerson
  03-partners.md       -> Nx OrgOrganization
  04-policies.md       -> Nx OrgPolicy
  07-decisions.md      -> Nx OrgDecision
  08-knowledge-assets.md -> Nx OrgKnowledgeAsset (Markdown-Tabelle)
  brain.json           -> OrgOffering + OrgEngagement + OrgOrganization
  ../../../../active/*/README.md (Front-Door, Geschwister-Repo Projekte/)
                        -> OrgEngagement (Frontmatter mit id: eng:*)

Aufruf:
  ./run.sh                 # Nodes committen (idempotent) + L1-Ingest
  ./run.sh --dry-run       # nur parsen + anzeigen, nichts committen
  ./run.sh --skip-l1       # Nodes committen, aber nicht in Qdrant content ingesten
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

import frontmatter
import httpx
import yaml
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest-agent")

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJEKTE_ROOT = REPO_ROOT.parent
SEED_ROOT = REPO_ROOT / "customers" / "nextchapter" / "knowledge" / "seed"
ACTIVE_ROOT = PROJEKTE_ROOT / "active"

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://127.0.0.1:8091")
TENANT_ID = os.environ.get("AIOS_TENANT_ID", "nextchapter")
PRODUCED_BY = "ingest-agent"

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
CONTENT_COLLECTION = os.environ.get("QDRANT_COLLECTION_CONTENT", "content")
EMBED_MODEL = os.environ.get(
    "SEARCH_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

FENCED_YAML_RE = re.compile(r"```yaml\n---\n(.*?)\n---\n```", re.DOTALL)
HEADING_RE = re.compile(r"^#{1,3}\s+(.+?)\s*$", re.MULTILINE)
BOLD_FIELD_RE = re.compile(r"\*\*Name:\*\*\s*(.+)")


def _split_yaml_blocks(text: str) -> list[tuple[dict[str, Any], str]]:
    """Liefert (yaml_dict, nachfolgender_text_bis_zum_naechsten_block)."""
    matches = list(FENCED_YAML_RE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        data = yaml.safe_load(m.group(1)) or {}
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        following = text[m.end():end]
        blocks.append((data, following))
    return blocks


def _first_heading(text: str) -> str | None:
    m = HEADING_RE.search(text)
    return m.group(1).strip() if m else None


def _first_name_field(text: str) -> str | None:
    m = BOLD_FIELD_RE.search(text)
    return m.group(1).strip() if m else None


def _titleize(id_str: str) -> str:
    tail = id_str.split(":", 1)[-1]
    return tail.replace("-", " ").title()


# --------------------------------------------------------------------------
# Parser je Seed-Quelle -> Liste von (node_type, payload_dict)
# --------------------------------------------------------------------------


def parse_organization() -> list[tuple[str, dict[str, Any]]]:
    path = SEED_ROOT / "00-organization.md"
    post = frontmatter.load(path)
    meta = post.metadata
    return [
        (
            "org:Organization",
            {"org_id": meta["id"], "name": meta["name"], "kind": meta.get("kind", "internal")},
        )
    ]


def parse_offerings() -> list[tuple[str, dict[str, Any]]]:
    text = (SEED_ROOT / "01-offerings.md").read_text(encoding="utf-8")
    out = []
    for data, following in _split_yaml_blocks(text):
        name = _first_name_field(following) or _titleize(data["id"])
        out.append(
            (
                "org:Offering",
                {"offering_id": data["id"], "name": name, "kind": data.get("kind", "product")},
            )
        )
    return out


def parse_people() -> list[tuple[str, dict[str, Any]]]:
    text = (SEED_ROOT / "02-people.md").read_text(encoding="utf-8")
    out = []
    for data, following in _split_yaml_blocks(text):
        name = _first_heading(following) or _titleize(data["id"])
        out.append(
            (
                "org:Person",
                {
                    "person_id": data["id"],
                    "name": name,
                    "role": data.get("role"),
                    "email": data.get("email"),
                },
            )
        )
    return out


def parse_partners() -> list[tuple[str, dict[str, Any]]]:
    text = (SEED_ROOT / "03-partners.md").read_text(encoding="utf-8")
    out = []
    for data, following in _split_yaml_blocks(text):
        name = _first_heading(following) or _titleize(data["id"])
        out.append(
            (
                "org:Organization",
                {"org_id": data["id"], "name": name, "kind": data.get("kind", "partner")},
            )
        )
    return out


def parse_policies() -> list[tuple[str, dict[str, Any]]]:
    text = (SEED_ROOT / "04-policies.md").read_text(encoding="utf-8")
    out = []
    for data, following in _split_yaml_blocks(text):
        title = _first_heading(following) or _titleize(data["id"])
        applies_to = data.get("applies_to") or []
        scope = "; ".join(applies_to) if applies_to else "global"
        out.append(
            (
                "org:Policy",
                {
                    "policy_id": data["id"],
                    "title": title,
                    "scope": scope,
                    "applies_to_refs": applies_to,
                },
            )
        )
    return out


def parse_decisions() -> list[tuple[str, dict[str, Any]]]:
    text = (SEED_ROOT / "07-decisions.md").read_text(encoding="utf-8")
    out = []
    for data, following in _split_yaml_blocks(text):
        title = _first_heading(following) or _titleize(data["id"])
        out.append(
            (
                "org:Decision",
                {
                    "decision_id": data["id"],
                    "title": title,
                    "status": data.get("status", "proposed"),
                    "decided_at": _normalize_date(data.get("decided_at")),
                    "summary": data.get("summary", title),
                    "about_refs": data.get("about") or [],
                },
            )
        )
    return out


def _normalize_date(value: Any) -> str | None:
    if not value:
        return None
    s = str(value)
    if re.fullmatch(r"\d{4}-\d{2}", s):
        return f"{s}-01"
    return s


def parse_knowledge_assets() -> list[tuple[str, dict[str, Any]]]:
    text = (SEED_ROOT / "08-knowledge-assets.md").read_text(encoding="utf-8")
    out = []
    for line in text.splitlines():
        if not line.startswith("|") or "asset_id" in line or set(line.replace("|", "").strip()) <= {"-"}:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) != 4:
            continue
        asset_id, title, orig_path, about = cols
        asset_id = asset_id.strip("`")
        if not asset_id.startswith("asset:"):
            continue
        refs = [r.strip().strip("`") for r in re.split(r"[+,]", about) if r.strip().strip("`").count(":") == 1]
        out.append(
            (
                "org:KnowledgeAsset",
                {
                    "asset_id": asset_id,
                    "title": title,
                    "path": orig_path.strip("`"),
                    "kind": "document",
                    "documents_refs": refs,
                    "published": True,
                },
            )
        )
    return out


def parse_brain_json() -> list[tuple[str, dict[str, Any]]]:
    path = SEED_ROOT / "brain.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[tuple[str, dict[str, Any]]] = []
    for org in data.get("organizations", []):
        out.append(("org:Organization", {"org_id": org["id"], "name": org["name"], "kind": org.get("kind", "internal")}))
    for off in data.get("offerings", []):
        out.append(
            (
                "org:Offering",
                {"offering_id": off["id"], "name": off["name"], "kind": off.get("kind", "product"), "summary": off.get("summary")},
            )
        )
    for eng in data.get("engagements", []):
        out.append(
            (
                "org:Engagement",
                {
                    "engagement_id": eng["id"],
                    "title": eng["title"],
                    "status": eng.get("status", "pipeline"),
                    "org_ref": eng.get("org_id"),
                    "offering_ref": eng.get("offering_id"),
                },
            )
        )
    return out


def parse_frontdoor_engagements() -> list[tuple[str, dict[str, Any]]]:
    """Front-Door-READMEs unter Projekte/active/*/README.md mit `id: eng:*`."""
    out = []
    if not ACTIVE_ROOT.exists():
        return out
    for readme in sorted(ACTIVE_ROOT.glob("*/README.md")):
        try:
            post = frontmatter.load(readme)
        except Exception:
            continue
        meta = post.metadata
        eid = meta.get("id")
        if not eid or not str(eid).startswith("eng:"):
            continue
        out.append(
            (
                "org:Engagement",
                {
                    "engagement_id": eid,
                    "title": meta.get("title", _titleize(eid)),
                    "status": meta.get("status", "active"),
                    "offering_ref": meta.get("offering"),
                },
            )
        )
    return out


def collect_all() -> list[tuple[str, dict[str, Any]]]:
    dps: list[tuple[str, dict[str, Any]]] = []
    dps += parse_organization()
    dps += parse_partners()
    dps += parse_people()
    dps += parse_brain_json()
    dps += parse_frontdoor_engagements()
    dps += parse_offerings()
    dps += parse_policies()
    dps += parse_decisions()
    dps += parse_knowledge_assets()
    return dps


# --------------------------------------------------------------------------
# Commit + L1-Ingest
# --------------------------------------------------------------------------


def commit_all(dps: list[tuple[str, dict[str, Any]]], dry_run: bool) -> list[dict[str, Any]]:
    results = []
    with httpx.Client(timeout=30.0) as client:
        for node_type, payload in dps:
            req = {
                "node_type": node_type,
                "tenant_id": TENANT_ID,
                "produced_by": PRODUCED_BY,
                "payload": payload,
                "dry_run": dry_run,
            }
            resp = client.post(f"{ORCHESTRATOR_URL}/v1/dataproduct/commit", json=req)
            if resp.status_code >= 400:
                log.error("Commit fehlgeschlagen %s %s: %s", node_type, payload.get("asset_id") or payload, resp.text)
                continue
            result = resp.json()
            result["_node_type"] = node_type
            result["_payload"] = payload
            results.append(result)
            log.info(
                "Committed %s %s -> node %s (%d Kanten, %d uebersprungen)",
                node_type,
                result.get("external_id"),
                result.get("node_id"),
                result.get("edges_created", 0),
                len(result.get("edges_skipped", [])),
            )
    return results


def _extract_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in {".md", ".markdown"}:
        try:
            return frontmatter.loads(raw).content
        except Exception:
            return raw
    return raw


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def ingest_knowledge_assets_to_l1(results: list[dict[str, Any]]) -> None:
    published = [
        r for r in results if r.get("_node_type") == "org:KnowledgeAsset" and r.get("ingest_queued") and not r.get("dry_run")
    ]
    if not published:
        log.info("Keine published KnowledgeAssets fuer L1-Ingest.")
        return

    embedder = TextEmbedding(model_name=EMBED_MODEL)
    dim = len(list(embedder.embed(["dimensionscheck"]))[0])
    client = QdrantClient(url=QDRANT_URL)
    existing = {c.name for c in client.get_collections().collections}
    if CONTENT_COLLECTION not in existing:
        log.info("Erstelle Qdrant-Collection '%s' (dim=%d)", CONTENT_COLLECTION, dim)
        client.create_collection(
            collection_name=CONTENT_COLLECTION,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )

    total_chunks = 0
    for r in published:
        payload = r["_payload"]
        rel_path = payload["path"]
        resolved = None
        for candidate in (REPO_ROOT / rel_path, PROJEKTE_ROOT / rel_path):
            if candidate.is_file():
                resolved = candidate
                break
        if resolved is None:
            log.warning(
                "KnowledgeAsset %s: keine lesbare Datei unter %s (Verzeichnis oder fehlend) - ueberspringe L1-Ingest",
                payload["asset_id"],
                rel_path,
            )
            continue

        text = _extract_text(resolved)
        chunks = _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        if not chunks:
            continue

        # Alte Chunks dieses Assets entfernen (Re-Ingest-Idempotenz)
        client.delete(
            collection_name=CONTENT_COLLECTION,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(must=[qm.FieldCondition(key="asset_id", match=qm.MatchValue(value=payload["asset_id"]))])
            ),
        )

        vectors = list(embedder.embed(chunks))
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"content://{payload['asset_id']}#{i}"))
            points.append(
                qm.PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload={
                        "source": "content",
                        "asset_id": payload["asset_id"],
                        "title": payload["title"],
                        "source_path": rel_path,
                        "node_id": r.get("node_id"),
                        "chunk_index": i,
                        "chunk_count": len(chunks),
                        "text": chunk,
                        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    },
                )
            )
        client.upsert(collection_name=CONTENT_COLLECTION, points=points)
        total_chunks += len(chunks)
        log.info("L1-Ingest: %s (%d Chunks)", payload["asset_id"], len(chunks))

    log.info("L1-Ingest fertig: %d Assets, %d Chunks gesamt.", len(published), total_chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-l1", action="store_true")
    args = parser.parse_args()

    dps = collect_all()
    log.info("Geparst: %d DataProducts aus Seed-Quellen.", len(dps))
    results = commit_all(dps, dry_run=args.dry_run)

    if not args.dry_run and not args.skip_l1:
        ingest_knowledge_assets_to_l1(results)

    stats_summary: dict[str, int] = {}
    for r in results:
        stats_summary[r["_node_type"]] = stats_summary.get(r["_node_type"], 0) + 1
    log.info("Zusammenfassung: %s", stats_summary)


if __name__ == "__main__":
    main()
