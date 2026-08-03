# content/knowledge — Firmenwissen & Dokumenten-Ablage

In diesem Verzeichnis hinterlegen Sie **offizielle Unternehmensdokumente**, die vom VIRKI AI-OS v2 automatisch indiziert und im Knowledge Graph verknüpft werden.

## 📂 Unterordner-Struktur

- **`vertraege/`**: Vertragsvorlagen, Mandantenvereinbarungen, Partnerverträge (PDF, Markdown).
- **`richtlinien/`**: AGBs, Datenschutzrichtlinien, Betriebsvereinbarungen, Gewährleistungsregeln.
- **`kalkulation/`**: Stundensätze, Materialaufschläge, Preistabellen, Kalkulationsgrundlagen (YAML, CSV, MD).

---

## ⚡ Automatische Verarbeitung

Sobald Sie hier eine Datei ablegen (z. B. `vertraege/Mustervertrag_Kunde.pdf`), erfasst das System den Text, indiziert ihn in der Volltextsuche (`memory.db`) und erstellt den entsprechenden Wissens-Knoten (`org:KnowledgeAsset`) im Knowledge Graph.
