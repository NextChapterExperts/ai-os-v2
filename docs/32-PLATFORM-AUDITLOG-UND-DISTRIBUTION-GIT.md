# docs/32-PLATFORM-AUDITLOG-UND-DISTRIBUTION-GIT.md — Plattform Auditlog & GitHub Distribution Repository

> **Architektur-Spezifikation für Release-Auditlog, Revisionssicherheit und Git-Distribution**  
> **Distributions-Repository:** `https://github.com/NextChapterExperts/virgi-platform-dist.git`

---

## 🎯 1. Ziel & Revisionssicherheit

Die AI-OS Core Platform bietet vollständige Nachvollziehbarkeit:
1. **Release-Auditlog:** Transparenter Changelog zwischen Release-Ständen (`v1.0.0`, `v1.1.0` etc.) direkt in der Web-UI (`/platform`).
2. **Operations-Auditlog:** Protokollierung aller administrativen Systemereignisse (Profil-Änderungen, Tenant-Erstellung, Ingest-Batches).
3. **GitHub Distribution:** Automatischer Push aus `export-core-appliance.sh` in das dedizierte Kunden- und Appliance-Repository `virgi-platform-dist`.

---

## 📦 2. Releaseregister Struktur (`core/orchestrator/releases.json`)

Jedes Release wird maschinenlesbar mit Metadaten hinterlegt:
- Version & Semantic Tag
- Release Datum & Uhrzeit
- Liste der Änderungen (Features, Performance, Bugfixes)
- Git Commit SHA
