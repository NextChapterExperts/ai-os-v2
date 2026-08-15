# VIRKI AI-OS v2 — Spezifikation: Papers Architect Agent (Fach-Agent)

> **Stand:** 2026-08-14 · **Status:** High-Priority Flagship Fach-Agent Spezifikation  
> **Bezug:** [12-LEITPRINZIPIEN.md](12-LEITPRINZIPIEN.md) (P5, P8, P15, P17, P18) · [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md) · [23-DOCKER-MCP-SANDBOX-INTEGRATION.md](23-DOCKER-MCP-SANDBOX-INTEGRATION.md) · [ROADMAP.md](../ROADMAP.md) (Kapitel 9, §9.6)

---

## 🎯 1. Übersicht & Zielsetzung

Der **Papers Architect Agent** ist der erste vollständig spezifizierte Fach-Agent für **VIRKI AI-OS v2**. Seine Aufgabe ist die Erstellung, Überprüfung, Übersetzung und revisionssichere Publikation wissenschaftlicher Arbeiten, technischer Referenz-Spezifikationen (RFCs) und Architektur-Whitepaper in Deutsch und Englisch (*Plain Business & Engineering English*).

Der Agent verarbeitet Rohentwürfe, Ideen, Code-Snippets und SAP BTP Architektur-Invarianten und überführt diese über eine **2-Pipeline-Architektur** in veröffentlichungsreife PDFs, Vektorgrafiken und Markdown-Manuskripte.

---

## 🏗️ 2. System-Architektur & Prinzipien-Konformität

Der Papers Architect Agent fügt sich strikt in den **AI-OS v2 Core Stack** ein:

```text
                                  Nutzer / Console UI / Obsidian
                                                 │
                                                 ▼ (POST /v1/dispatch)
                               ┌───────────────────────────────────┐
                               │ Orchestrator (core/orchestrator/) │
                               │  • Intent: CREATE_PAPER           │
                               │  • Context Bundle (6 Slices)      │
                               └─────────────────┬─────────────────┘
                                                 │
                                                 ▼
                               ┌───────────────────────────────────┐
                               │ agents/papers/paper_architect.py  │
                               └─────────┬───────────────┬─────────┘
                                         │               │
                 ┌───────────────────────┘               └────────────────────────┐
                 ▼ (self.mcp.call)                                                ▼ (PGE Trinity Sandbox)
┌─────────────────────────────────────────┐                     ┌──────────────────────────────────────────┐
│ MCP Gateway & Docker MCP Stack (P5)     │                     │ Docker MicroVM Sandbox (P15)             │
│  • mcp_arxiv (Preprints)                │                     │  • Python Matplotlib (300 DPI Figures)   │
│  • docker_brave_search (IEEE/ACM Web)   │                     │  • Typst CLI Compiler (Sandboxed PDF)    │
│  • mcp_sap_docs (SAP BTP Specs)         │                     │  • Pangram 4.0 Humanization Scan         │
└────────────────────┬────────────────────┘                     └────────────────────┬─────────────────────┘
                     │                                                               │
                     └───────────────────────────┬───────────────────────────────────┘
                                                 │
                                                 ▼ (POST /v1/dataproduct/commit)
                               ┌───────────────────────────────────┐
                               │ DataProduct Service (P18)         │
                               │  • ResearchSourceSet              │
                               │  • PaperSpecification             │
                               │  • PaperArtifact                  │
                               └─────────────────┬─────────────────┘
                                                 │
                        ┌────────────────────────┼────────────────────────┐
                        ▼                        ▼                        ▼
               [G: Knowledge Graph]    [K: File System]         [A: SHA-256 Audit Ledger]
               Node: org:KnowledgeAsset content/papers/         ai_os_log / run_receipts
```

---

## 📦 3. DataProduct-Spezifikationen (Prinzip P18)

Jeder Input, Zwischenschritt und Output des Papers Architect Agent ist ein typisiertes **DataProduct**. Direkte Schreibzugriffe auf Datenbanken oder Dateien aus dem Agenten sind untersagt.

```python
# agents/papers/schemas.py
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from sdk.dataproduct import DataProduct

class ResearchSourceItem(BaseModel):
    title: str
    authors: list[str]
    source_type: Literal["arxiv", "ieee", "acm", "sap_doc", "mcp_spec"]
    url: str
    doi_or_arxiv_id: str | None = None
    abstract_summary: str

class ResearchSourceSet(DataProduct):
    """Vom MCP Gateway geerntete Recherche-Quellen."""
    produced_by = "paper-architect-agent"
    storage_target = ["G", "L1"]        # Knowledge Graph + Qdrant Vector Index
    ingest_recommended = True

    topic_slug: str
    sources: list[ResearchSourceItem]
    bibtex_content: str
    confidence: float = Field(ge=0.0, le=1.0)

class PaperSpecification(DataProduct):
    """Inhaltliche Papier-Spezifikation (Axiome, Gliederung & Metadaten)."""
    produced_by = "paper-architect-agent"
    storage_target = ["G", "K"]         # Knowledge Graph + File System (content/papers/)
    ingest_recommended = False

    topic_slug: str
    title_de: str
    title_en: str
    abstract_de: str
    abstract_en: str
    author_name: str = "Peter Alexander"
    author_role: str = "SAP BTP & Enterprise AI Architect | Specializing in Autonomous AI Agents & Integration Architecture"
    author_email: str = "peter.alexander@nextchapterexperts.de"
    author_orcid: str = "https://orcid.org/0009-0003-0512-0474"
    research_set_ref: str               # DP-ID des ResearchSourceSet
    axioms: list[str]
    compliance_status: Literal["draft", "aligned_with_author", "cleared"] = "draft"

class PaperArtifact(DataProduct):
    """Finale kompilierte Artefakte (PDF, Typst, Markdown, 300 DPI Grafiken)."""
    produced_by = "paper-architect-agent"
    storage_target = ["G", "K", "L1", "A"]   # Graph + File System + Qdrant + Audit Ledger
    ingest_recommended = True

    topic_slug: str
    spec_ref: str                            # DP-ID der PaperSpecification
    language: Literal["de", "en"]
    pdf_path: str                            # "content/papers/[slug]/[lang]/paper.pdf"
    typst_path: str
    markdown_path: str
    pangram_human_score: float               # Target >0.95 (Pangram 4.0 Standard)
    sha256_hash: str                         # SHA-256 Prüfsumme

class PaperBlogExtract(DataProduct):
    """Allgemeinverständliche Blog-Extraktion aus dem Paper für Website & LinkedIn."""
    produced_by = "paper-architect-agent"
    storage_target = ["G", "K", "L1"]        # Graph + File System (blog/) + Qdrant
    ingest_recommended = True

    topic_slug: str
    artifact_ref: str                        # DP-ID des PaperArtifact
    language: Literal["de", "en"]
    website_article_path: str                # "content/papers/[slug]/[lang]/blog/blog_website.md"
    linkedin_post_path: str                 # "content/papers/[slug]/[lang]/blog/blog_linkedin.md"
    target_channels: list[str] = ["website", "linkedin_feed", "linkedin_pulse"]
```

---

## 🔌 4. MCP Gateway & Docker MCP Stack Integration (Prinzip P5)

Für die externe Datenbank-Recherche ruft der Agent ausschließlich das **MCP Gateway** auf:

```python
# agents/papers/paper_architect.py (Ausschnitt)
class PaperArchitectAgent(AgentBase[PaperSpecification, PaperArtifact]):
    
    async def research_topic(self, topic: str) -> ResearchSourceSet:
        # Externe Recherche zwingend über self.mcp (P5)
        arxiv_results = await self.mcp.call("mcp_arxiv", action="search", query=topic)
        web_results = await self.mcp.call("docker_brave_search", query=f"{topic} IEEE enterprise architecture")
        sap_results = await self.mcp.call("mcp_sap_docs", query=topic)
        
        # Erzeugt typisiertes DataProduct
        return ResearchSourceSet(
            topic_slug=slugify(topic),
            sources=parse_sources(arxiv_results, web_results, sap_results),
            bibtex_content=build_bibtex(arxiv_results),
            confidence=0.92,
            tenant_id=self.ctx.tenant_id
        )
```

---

## 🛡️ 5. Sandbox Execution (Prinzip P15 - PGE Trinity)

Die Ausführung von Bildgenerierungsskripten (`matplotlib`) und PDF-Kompilierbefehlen (`typst compile`) erfolgt isoliert in ephemeren Docker MicroVM Sandboxes:

```python
# Ausführung im PGE Trinity Executor
executor_res = await self.executor.run_in_sandbox(
    image="virki/paper-build-runtime:latest",
    command=f"python3 make_figures_EN.py && typst compile --root / {typst_file} {pdf_file}",
    timeout_seconds=45,
    network_access=False  # Keine Netzwerkverbindung während des PDF-Builds
)
```

---

## 🔄 6. Die 3-Pipeline Arbeitsweise des Agenten

Der Agent steuert drei klar getrennte Pipelines:

### Pipeline 1: Inhaltliche Verarbeitung & Dialog-Recherche
1. **Context Harvesting:** Extrahiert Kernaussagen & Invarianten aus Rohentwürfen.
2. **Autonomous Research:** Abfragen über MCP Gateway (`mcp_arxiv`, `docker_brave_search`).
3. **Interactive Alignment:** Ausgabe von Gliederungs- und Axiom-Vorschlägen im Chat.
4. **Humanization Scan:** Verfasst den Text im Ego-Stil von Peter Alexander mit hoher Burstiness (Pangram Score $>95\%$).
5. **Translation:** Übersetzt in *Plain Business & Engineering English*.
6. **Web-Blog & LinkedIn Extraktion:** Erstellt allgemeinverständlichen Web-Blogartikel (`/blog/blog_post.md`) und kürzeren LinkedIn Post (`/linkedin/linkedin_post.md`) mit CTA-Link.

### Pipeline 2: Technische Umsetzung & Revisionssicherheit
1. **Workspace Isolation:** Erstellung von `content/papers/[slug]/de/` und `/en/`.
2. **300 DPI Figure Rendering:** Clockwise-Grid Matplotlib Engine in Sandbox.
3. **Typst Injection:** Typst-Code mit Autoren-Stammdaten, ORCID iD & `12pt Bold` Formeln.
4. **Sandboxed Compilation:** Erzeugung der PDFs ohne Host-Zugriff.
5. **SHA-256 Commit:** Schreiben der Hashes in `manifest.json` und Registrierung in Speicherschicht $\mathcal{S}_5$ (Audit).

### Pipeline 3: Publikation & Multi-Kanal-Distribution
1. **Zenodo Upload:** REST-API Upload $\to$ Erzeugung einer permanenten DOI (z. B. `10.5281/zenodo.XXXXXX`).
2. **ORCID Profil Update:** Verknüpfung der DOI mit Profil `0009-0003-0512-0474`.
3. **GitHub Release:** Release-Tagging und Asset-Upload im Repository `nextchapterexperts/enterprise-ai-papers`.
4. **Website Publishing:** Veröffentlichung von `/blog/blog_post.md` auf `nextchapterexperts.de`.
5. **LinkedIn Publishing:** Posten von `/linkedin/linkedin_post.md` mit CTA-Link zum Web-Blogartikel.
6. **SAP Community Syndication:** Veröffentlichung im SAP Community Network.

---

## 🧪 7. Test-Strategie & Abnahme-Kriterien

1. **Contract Test:** `tests/contract/test_paper_architect_contract.py` prüft, ob In/Out DataProducts schema-konform sind.
2. **MCP Isolation Test:** `tests/contract/test_paper_architect_mcp.py` stellt sicher, dass kein direkter HTTP-Outbound erfolgt.
3. **Pangram Humanization Test:** `tests/unit/test_pangram_filter.py` prüft Texte auf KI-Floskeln.
4. **Master Testrun:** `./scripts/run-all-tests.sh` muss 100% fehlerfrei durchlaufen.
