# Website Prototype Workaround & Quickstart Guide (`website-nce`)

> **Zweck dieses Dokumentes:** Dokumentation des lokalen Prototyping-Workarounds für das Projekt `website-nce` (`/home/peter/Projekte/active/website-nce`).

---

## 🚀 Lokalen Server starten & testen

Falls der Server gestoppt wird, kann er jederzeit mit folgenden Befehlen gestartet werden:

```bash
cd /home/peter/Projekte/active/website-nce
npx next dev -H 0.0.0.0 -p 3001
```

### 🌐 Lokale URLs

| Seite | Pfad | Beschreibung |
| :--- | :--- | :--- |
| **Root (Auto-Redirect)** | `http://localhost:3001/` | Leitet automatisch per HTTP 307 auf `/de/prototype/home` weiter |
| **Startseite** | `http://localhost:3001/de/prototype/home` | Hero-Split & 5 Leistungskacheln |
| **Beratung** | `http://localhost:3001/de/prototype/portfolio` | SAP Enablement & BTP Coaching |
| 🏰 **Produkte (VIRKI)** | `http://localhost:3001/de/prototype/virki` | VIRKI Corporate Appliance & Blueprint |
| **KI-Audit** | `http://localhost:3001/de/prototype/ki-audit` | KI-Architektur & Risikobewertung |
| **Lectures** | `http://localhost:3001/de/prototype/lectures` | Vorträge & Enterprise-Schulungen |
| **Blogs** | `http://localhost:3001/de/prototype/blog` | Blogartikel & Realpessimismus-Serie |
| **Kontakt** | `http://localhost:3001/de/prototype/contact` | Intent-basiertes Kontaktformular |

---

## 📐 Navigations- & Komponenten-Struktur

1. **`PrototypeSubnav.tsx`** (`src/components/prototype/PrototypeSubnav.tsx`):
   - Schlichte, elegante Navigation ohne schwere Fettschrift und ohne Emoji-Buzzwords:
     `Start` · `Beratung` · `Produkte` · `KI-Audit` · `Lectures` · `Blogs` · `Kontakt`

2. **`VirkiPage.tsx`** (`src/components/prototype/VirkiPage.tsx`):
   - **Above-The-Fold Definition:** Sofortige Einordnung von VIRKI als *Sovereign Enterprise Platform-VM & Appliance*.
   - **System-Specs Dashboard:** 100 % In-House, 85 % Ersparnis durch lokale LLM Inference, Krypto-Audit-Trail.
   - **Blueprint Artwork:** Druckoptimierte Skizze der VIRKI-Citadel (`/public/assets/virki_odin_sketchbook_bright.png`).
   - **Story & Mythologie:** Odin (Führung), Muninn (Gedächtnis) & Huginn (Workflow-Engine).
   - **10 Realitätsfallen:** Failing Silently, RAG-Drift, GoBD-Audit etc.

3. **`HomePrototype.tsx`** (`src/components/prototype/HomePrototype.tsx`):
   - Enthält 5 Kacheln inklusive des hervorgehobenen Produktes 🏰 **VIRKI**.

---

## ⚙️ Versionsstand & Git

- **Repository**: `/home/peter/Projekte/active/website-nce`
- **Branch**: `master` (Commit `40b7a8d`)
