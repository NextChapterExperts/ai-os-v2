#!/usr/bin/env bash
# ==============================================================================
# scripts/export-core-appliance.sh
# Exportiert die reine AI-OS v2 Core Plattform Appliance in ein autarkes
# Distributions-Projekt (1110-AI-OS-Core-Platform) ohne R&D-Artefakte.
# ==============================================================================
set -euo pipefail

SRC_DIR="/home/peter/Projekte/1100-AI-OS-V2"
TARGET_DIR="/home/peter/Projekte/1110-AI-OS-Core-Platform"

echo "🚀 Starte Export der Core Plattform Appliance..."
echo "📂 Quelle: ${SRC_DIR}"
echo "🎯 Ziel:   ${TARGET_DIR}"

# 1. Zielverzeichnis vorbereiten
mkdir -p "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}/core/orchestrator"
mkdir -p "${TARGET_DIR}/core/memory"
mkdir -p "${TARGET_DIR}/core/memory_gateway"
mkdir -p "${TARGET_DIR}/core/workflow_engine"
mkdir -p "${TARGET_DIR}/core/file_ingest_watcher"
mkdir -p "${TARGET_DIR}/core/ingest_agent"
mkdir -p "${TARGET_DIR}/core/console-web"
mkdir -p "${TARGET_DIR}/sdk"
mkdir -p "${TARGET_DIR}/config"
mkdir -p "${TARGET_DIR}/deploy"
mkdir -p "${TARGET_DIR}/tests"
mkdir -p "${TARGET_DIR}/docs"
mkdir -p "${TARGET_DIR}/scripts"

# 2. Core Plattform Backend-Module kopieren
echo "📦 Kopiere alle Core Plattform Backend-Module..."
rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/orchestrator/" "${TARGET_DIR}/core/orchestrator/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/memory/" "${TARGET_DIR}/core/memory/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/memory_gateway/" "${TARGET_DIR}/core/memory_gateway/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/workflow_engine/" "${TARGET_DIR}/core/workflow_engine/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' --exclude '.venv' \
  "${SRC_DIR}/core/file_ingest_watcher/" "${TARGET_DIR}/core/file_ingest_watcher/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/ingest_agent/" "${TARGET_DIR}/core/ingest_agent/"

# 3. Agent SDK & Schemas kopieren
echo "🧩 Kopiere Agent SDK & Developer Kit..."
rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/sdk/" "${TARGET_DIR}/sdk/"

# 4. Plattform-Konfigurationen kopieren
echo "⚙️ Kopiere Plattform-Konfigurationen & SQL-Schemata..."
rsync -av --exclude '__pycache__' \
  "${SRC_DIR}/config/" "${TARGET_DIR}/config/"

# 5. Deployment-Setups kopieren
echo "🐳 Kopiere Deployment-Setups & Docker Stacks..."
rsync -av "${SRC_DIR}/deploy/" "${TARGET_DIR}/deploy/"

# 6. Reines Web Frontend kopieren (Reine Plattform-Funktionalität)
echo "🌐 Kopiere Core Web Konsole (Next.js) & passe auf DIST an..."
rsync -av --exclude 'node_modules' --exclude '.next' --exclude '.git' \
  "${SRC_DIR}/core/console-web/" "${TARGET_DIR}/core/console-web/"

# Fachagenten & Provisionierungs-Routen aus DIST entfernen
rm -rf "${TARGET_DIR}/core/console-web/src/app/agents"
rm -rf "${TARGET_DIR}/core/console-web/src/app/platform/vms"
rm -rf "${TARGET_DIR}/core/console-web/src/app/workflows"
rm -rf "${TARGET_DIR}/core/console-web/src/app/api/agents"
rm -rf "${TARGET_DIR}/core/console-web/src/app/api/workflows"
rm -rf "${TARGET_DIR}/core/console-web/src/app/api/platform/gcp/vms"

# AppShell in DIST auf reinen Plattform-Modus & DIST-Badge anpassen
cat << 'EOF' > "${TARGET_DIR}/core/console-web/src/components/AppShell.tsx"
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getStoredAuth, logoutUser, switchRole, AuthUser } from "@/lib/auth";
import { IconLogout, IconUserCheck, IconShieldLock } from "@tabler/icons-react";

const USER_NAV = [
  { href: "/", label: "Lagebild" },
  { href: "/search", label: "Suche" },
] as const;

const ADMIN_NAV = [
  { href: "/", label: "Lagebild" },
  { href: "/company", label: "Unternehmen" },
  { href: "/search", label: "Suche" },
  { href: "/platform", label: "Plattform" },
] as const;

function matchLength(pathname: string, href: string): number {
  if (href === "/") return pathname === "/" ? 1 : 0;
  if (pathname === href || pathname.startsWith(`${href}/`)) return href.length;
  return 0;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [auth, setAuth] = useState<AuthUser | null>(null);

  useEffect(() => {
    setAuth(getStoredAuth());

    const handleAuthChange = () => {
      setAuth(getStoredAuth());
    };

    window.addEventListener("aios-auth-changed", handleAuthChange);
    return () => window.removeEventListener("aios-auth-changed", handleAuthChange);
  }, []);

  const isLoginPage = pathname === "/login";
  const navItems = auth?.role === "admin" ? ADMIN_NAV : USER_NAV;

  const bestMatch = navItems.reduce(
    (best, item) => {
      const len = matchLength(pathname, item.href);
      return len > best.len ? { href: item.href, len } : best;
    },
    { href: "", len: 0 },
  );

  const handleLogout = () => {
    logoutUser();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    } else {
      router.push("/login");
    }
  };

  if (isLoginPage) {
    return <main className="min-h-screen bg-[var(--paper)]">{children}</main>;
  }

  return (
    <div className="shell-bg">
      <header className="mx-auto flex w-full max-w-[1700px] items-center justify-between gap-4 px-6 pt-5 pb-2 sm:px-10">
        <div className="relative group/virki">
          <Link href="/" className="brand-mark no-underline flex items-center gap-2">
            <span className="text-xl sm:text-2xl text-signal group-hover/virki:scale-110 transition-transform font-bold" title="Wyrd-Key / Odins Raben">
              ᚢ
            </span>
            <span className="font-mystic text-2xl sm:text-3xl font-extrabold tracking-[0.16em] text-ink uppercase group-hover/virki:text-signal transition-colors">
              VIRKI
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-signal/15 text-signal border border-signal/30">
              DIST
            </span>
          </Link>

          {/* Odin's Ravens Story Hover Popover Dropdown */}
          <div className="absolute left-0 top-full mt-2 w-80 sm:w-96 rounded-xl border border-line bg-card/95 p-4 shadow-2xl backdrop-blur-md opacity-0 pointer-events-none group-hover/virki:opacity-100 group-hover/virki:pointer-events-auto transition-all duration-200 z-50">
            <div className="flex items-center gap-2 mb-2 border-b border-line pb-2">
              <span className="text-lg">🦅</span>
              <h4 className="font-bold text-sm text-ink m-0">VIRKI & Die Raben von Odin</h4>
            </div>
            <p className="text-xs text-ink-soft leading-relaxed mb-2">
              Es war einmal Odin, der Gott der Weisheit, der sein Reich von der Festung <strong className="text-ink">VIRKI</strong> aus regierte. An seiner Seite dienten zwei treue Raben:
            </p>
            <ul className="text-xs text-ink-soft space-y-1 pl-1 list-none mb-2">
              <li className="flex items-start gap-1.5">
                <span>🦅</span>
                <span><strong className="text-ink">MUNINN</strong> <em>(Das Gedächtnis)</em>: Fliegt täglich aus, erfasst Mails, Chats & Wissen und bewahrt es unvergesslich auf.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span>🦅</span>
                <span><strong className="text-ink">HUGINN</strong> <em>(Der Gedanke)</em>: Blickt in die Zukunft, durchdenkt Strategien & führt autonome KI-Workflows aus.</span>
              </li>
            </ul>
            <p className="text-[11px] text-muted italic m-0 pt-1 border-t border-line/50">
              VIRKI vereint Gedächtnis, Gedanke & souveräne Kontrolle in Ihrem KI-Betriebssystem.
            </p>
          </div>
        </div>

        <nav className="flex flex-wrap items-center gap-4 text-sm sm:gap-6 sm:text-base">
          {navItems.map((item) => {
            const active = bestMatch.len > 0 && item.href === bestMatch.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="nav-link"
                data-active={active ? "true" : "false"}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-3 text-right text-xs text-ink-soft">
          {auth ? (
            <div className="flex items-center gap-2 bg-[color-mix(in_oklab,white_85%,transparent)] border border-[var(--line)] rounded-xl px-2.5 py-1 text-xs">
              <button
                type="button"
                onClick={() => switchRole(auth.role === "admin" ? "user" : "admin")}
                className="flex items-center gap-1.5 hover:opacity-80 transition-opacity cursor-pointer text-left"
                title={`Klicken um zu ${auth.role === "admin" ? "Endanwender" : "Admin"} zu wechseln`}
              >
                {auth.role === "admin" ? (
                  <IconShieldLock size={14} className="text-amber-500" />
                ) : (
                  <IconUserCheck size={14} className="text-[var(--signal)]" />
                )}
                <span className="font-bold text-[var(--ink)]">
                  {auth.username} ({auth.role === "admin" ? "Admin" : "Endanwender"})
                </span>
                <span className="text-[10px] text-signal font-mono uppercase bg-signal/10 px-1 py-0.5 rounded">
                  ⇄ Wechseln
                </span>
              </button>
              <button
                type="button"
                onClick={handleLogout}
                className="btn-ghost py-0.5 px-1.5 text-[11px] text-danger hover:underline inline-flex items-center gap-1 cursor-pointer ml-1"
                title="Abmelden"
              >
                <IconLogout size={12} />
              </button>
            </div>
          ) : (
            <Link href="/login" className="btn-ghost text-xs font-bold text-[var(--signal)]">
              Anmelden
            </Link>
          )}
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1700px] px-4 pb-16 sm:px-10">{children}</main>
    </div>
  );
}
EOF

# 7. Plattform-Testsuite kopieren
echo "🧪 Kopiere Plattform-Testsuite..."
rsync -av --exclude '__pycache__' --exclude '.pytest_cache' \
  "${SRC_DIR}/tests/" "${TARGET_DIR}/tests/"

# 8. Konfigurations- & Root-Dateien kopieren
if [ -f "${SRC_DIR}/core/orchestrator/requirements.txt" ]; then
  cp -f "${SRC_DIR}/core/orchestrator/requirements.txt" "${TARGET_DIR}/requirements.txt"
fi
if [ -f "${SRC_DIR}/.env.example" ]; then
  cp -f "${SRC_DIR}/.env.example" "${TARGET_DIR}/"
fi
if [ -f "${SRC_DIR}/.gitignore" ]; then
  cp -f "${SRC_DIR}/.gitignore" "${TARGET_DIR}/"
fi

# 9. Vollständige CLI & Speichermanagement-Skripte kopieren
echo "🛠️ Kopiere alle Speichermanagement-, Ingest-, Test- & Plattform-Skripte..."
SCRIPTS_TO_EXPORT=(
  "run-all-tests.sh"
  "run-l1-curator.py"
  "run-l2-curator.py"
  "run-l3-curator.py"
  "rebuild-fts.py"
  "backfill-letta-from-sqlite.py"
  "provision-tenant.sh"
  "search_company_brain.py"
  "manage_memory.py"
  "ingest_documents.py"
  "manage_company_profile.py"
  "run-memory-testcases.py"
  "generate-memory-testcases.py"
  "run-compute-mode-testcases.py"
)

for s in "${SCRIPTS_TO_EXPORT[@]}"; do
  if [ -f "${SRC_DIR}/scripts/${s}" ]; then
    cp -f "${SRC_DIR}/scripts/${s}" "${TARGET_DIR}/scripts/"
  fi
done
chmod +x "${TARGET_DIR}"/scripts/*

# 6. Vollständige Original-Plattform-Dokumentation kopieren
echo "📚 Kopiere alle vollständigen Original-Dokumente aus docs/..."

DOC_FILES=(
  "00-VISION.md"
  "01-ARCHITEKTUR.md"
  "02-AGENT-SDK.md"
  "03-DATENPRODUKTE.md"
  "04-DEPLOYMENT.md"
  "05-CONSOLE-IA.md"
  "06-PRODUKT-DEPLOYMENT.md"
  "07-LOKALES-MODELL-TESTPROTOKOLL.md"
  "08-MARKTVERGLEICH.md"
  "09-COMPANY-BRAIN.md"
  "10-MEMORY-EINFACH.md"
  "11-PLATFORM-VM.md"
  "12-LEITPRINZIPIEN.md"
  "13-IST-STAND.md"
  "14-KONTEXT.md"
  "15-FILE-INGESTION.md"
  "16-VM-PACKAGING.md"
  "22-RELEASE-TAGS.md"
  "23-DOCKER-MCP-SANDBOX-INTEGRATION.md"
  "25-COMPANY-BRAIN-MEMORY-MAPPING.md"
  "26-ARTEN-VON-RAG.md"
  "27-ROLLEN-UND-RECHTE-KONZEPT.md"
  "28-PLATFORM-VS-CUSTOM-AGENTS-MODELL.md"
  "29-STAGING-UND-VM-RELEASE-WORKFLOW.md"
  "30-CORE-PLATFORM-EXTRACTION-UND-DOCKER-CONTAINER.md"
  "31-CORE-PLATFORM-DISTRIBUTION-REPO.md"
  "32-PLATFORM-AUDITLOG-UND-DISTRIBUTION-GIT.md"
  "company_brain_paper_DE.pdf"
)

for doc in "${DOC_FILES[@]}"; do
  if [ -f "${SRC_DIR}/docs/${doc}" ]; then
    cp -f "${SRC_DIR}/docs/${doc}" "${TARGET_DIR}/docs/"
  fi
done

if [ -d "${SRC_DIR}/docs/adr" ]; then
  rsync -av "${SRC_DIR}/docs/adr/" "${TARGET_DIR}/docs/adr/"
fi

# Zusätzliches Handbuch für CLI Tools
cat << "EOF" > "${TARGET_DIR}/docs/00-CLI-UND-ADMIN-HANDBUCH.md"
# 00 — CLI- & Administrations-Handbuch

Die Plattform verfügt über dedizierte Skripte im Verzeichnis \`scripts/\`:

### 1. Wissenssuche im Terminal (\`scripts/search_company_brain.py\`)
\`\`\`bash
python3 scripts/search_company_brain.py "Welche Zahlungsfristen gelten für Großkunden?" --tenant default
\`\`\`

### 2. Memory- & Speicherverwaltung (\`scripts/manage_memory.py\`)
\`\`\`bash
python3 scripts/manage_memory.py --status
\`\`\`

### 3. Dokumenten- & PDF-Ingestion (\`scripts/ingest_documents.py\`)
\`\`\`bash
# Einzelne Datei ingestieren
python3 scripts/ingest_documents.py /pfad/zum/vertrag.pdf --tenant default

# Ganzen Ordner batch-ingestieren
python3 scripts/ingest_documents.py /pfad/zu/dokumenten/ --tenant default
\`\`\`

### 4. Firmenprofil per CLI (\`scripts/manage_company_profile.py\`)
\`\`\`bash
# Profil anzeigen
python3 scripts/manage_company_profile.py --tenant default

# Profil aktualisieren
python3 scripts/manage_company_profile.py --update-from neues_profil.yaml --tenant default
\`\`\`
EOF

# 7. Readme für das Distributions-Repo
cat << "EOF" > "${TARGET_DIR}/README.md"
# AI-OS Core Platform Appliance (v1.0.0)

> **Sovereign Enterprise Memory & Knowledge Platform**  
> Offizielles Distributions-Repository der reinen AI-OS Core Appliance.

## 🚀 Schnellstart

\`\`\`bash
# Docker Stack starten
cd deploy/docker
docker compose up -d
\`\`\`

- **Web-Konsole:** [http://localhost:8090](http://localhost:8090)
- **Orchestrator API:** [http://localhost:8091/docs](http://localhost:8091/docs)

## 🛠️ CLI & Management Werkzeuge

- **Suche im Unternehmenswissen:** `python3 scripts/search_company_brain.py "<Query>"`
- **Speicherstatus & Memory Stacks:** `python3 scripts/manage_memory.py --status`
- **Dokumenten-Ingestion:** `python3 scripts/ingest_documents.py <Pfad>`
- **Unternehmensprofil:** `python3 scripts/manage_company_profile.py`

## 📚 Dokumentation
Die vollständige Architektur-Dokumentation befindet sich im Verzeichnis [`docs/`](docs/).
EOF

# 8. Git Sync & GitHub Distribution Push
cd "${TARGET_DIR}"
git branch -M main || true
TOKEN=$(git -C "${SRC_DIR}" config --get remote.origin.url | sed -n 's/.*x-access-token:\([^@]*\)@.*/\1/p' || true)
if [ -n "${TOKEN}" ]; then
  AUTH_REMOTE="https://x-access-token:${TOKEN}@github.com/NextChapterExperts/virgi-platform-dist.git"
else
  AUTH_REMOTE="https://github.com/NextChapterExperts/virgi-platform-dist.git"
fi

if ! git remote | grep -q "origin"; then
  git remote add origin "${AUTH_REMOTE}"
else
  git remote set-url origin "${AUTH_REMOTE}"
fi

git add .
git commit -m "feat(release): AI-OS Core Platform Appliance v1.0.0

- Revisionssicherer Release-Changelog & Auditlog
- 5-Schichten-Memory-Modell & Hybrid Graph-RAG
- Unternehmens-Identität & Dynamische Profilverwaltung (/company)
- Multi-Stage Dockerfile & Docker Compose Setup
- CLI Management Toolbox (search, memory, ingest, company profile)
- Vollständige Architektur- & Kunden-Dokumentation (docs/01-06)" || true

git tag -f v1.0.0-core-appliance -m "AI-OS Core Platform Appliance v1.0.0"

echo "📡 Pushe Release nach GitHub (virgi-platform-dist)..."
git push -u origin main --tags --force

echo "✅ Core Plattform Appliance & CLI-Skripte erfolgreich nach ${TARGET_DIR} exportiert und gepusht!"
