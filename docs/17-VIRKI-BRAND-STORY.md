# VIRKI — Das Brand-Book & Plattform-Mapping

> **Markenkern:** *Ein System. Zwei Raben. Volle Souveränität.*  
> **Stand:** 2026-07-26 · Next Chapter Experts (`nextchapter`)

---

![VIRKI — Die souveräne KI-Festung mit Odin, Huginn & Muninn (Print-Friendly Sketchbook Blueprint)](file:///home/peter/Projekte/1100-AI-OS-V2/docs/assets/virki_odin_sketchbook_bright.png)

---

## 📜 1. Die Mythologische Legende

In den alten Hallen des Nordens herrschte Allvater **Odin**, der Sucher nach absoluter Weisheit. Er wusste, dass Macht ohne Wissen blind ist und dass Gedanken ohne Gedächtnis verfliegen wie Rauch im Wind.

Um sein Reich vor Chaos und Vergessen zu schützen, schuf Odin ein Heiligtum: **VIRKI** — eine unüberwindbare, souveräne Festung aus Stein und Schutzwällen, in der kein Fremder ungebeten Zutritt fand.

Auf den Zinnen von Virki saßen Odins zwei treueste Gefährten:

- 🦅 **MUNINN** — *Das unbestechliche Gedächtnis.*  
  Jeden Morgen bei Sonnenaufgang flog Muninn lautlos über alle neun Welten. Er beobachtete jedes Gespräch, zeichnete jeden Schwur auf, sah jede Entscheidung und vergaß keinen einzigen Moment. Wenn der Tag sich neigte, kehrte Muninn nach Virki zurück und legte das gesammelte Wissen sicher im tiefen Gewölbe der Festung ab.
- 🦅 **HUGINN** — *Der scharfsinnige Gedanke.*  
  Während Muninn das Bewahrte hütete, blickte Huginn in die Zukunft. Er wog Optionen ab, durchdrang komplexe Zusammenhänge, durchdachte Strategien und schmiedete scharfschneidige Pläne.

Wenn Odin eine Entscheidung treffen musste, traten beide Raben an seine Seite:  
**Muninn flüsterte ihm die unumstößlichen Fakten der Vergangenheit ins Ohr**, und **Huginn webte daraus den perfekten Gedanken für die Zukunft.**

In der Festung **Virki** vereinten sich so Gedächtnis, Gedanke und Führung zu unbesiegbarer Souveränität.

---

## ⚔️ 2. Das System-Mapping auf die Plattform

| Mythologischer Part | Plattform-Komponente | Technische Realisierung & Prinzipien |
| :--- | :--- | :--- |
| **VIRKI** *(Die Festung)* | **Platform-VM & Appliance** | • 100 % In-House / On-Premise (P19)<br>• Physische & logische Mandantentrennung<br>• Zero Data Leakage an US-Cloud-Server |
| 🦅 **MUNINN** *(Das Gedächtnis)* | **Company Brain & Capture** | • Chat Capture aus Cursor, Antigravity & Gemini<br>• Knowledge Graph (`org:*`), Qdrant & FTS5<br>• Episodisches & taktisches Gedächtnis (L0–L3) |
| 🦅 **HUGINN** *(Der Gedanke)* | **Agentic Workflows & LLM Engine** | • LangGraph Workflow-Engine & Agenten-Flotte<br>• 80–90 % lokale LLM-Inference (€0 Token-Kosten, P12)<br>• Intent-Routing & automatische Task-Synthese |
| **ODIN** *(Der Lenker)* | **Benutzer & Console UI** | • Ebene 1 Lagebild für tägliche Führung (P1)<br>• Mensch entscheidet, Raben arbeiten zu<br>• Volle Kontrolle über Freigaben & Sichtbarkeit |

---

## 🏛️ 3. Architektur-Diagramm

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ VIRKI PLATFORM-VM (Die souveräne Festung)                              │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      ODIN CONSOLE (Ebene 1)                     │   │
│   └────────────────────────────────┬────────────────────────────────┘   │
│                                    │                                    │
│             ┌──────────────────────┴──────────────────────┐             │
│             ▼                                             ▼             │
│   🦅 HUGINN ENGINE (Der Gedanke)              🦅 MUNINN ENGINE (Memory)  │
│   • LangGraph Workflows                       • Company Brain Graph    │
│   • Agenten-Flotte (Research, Blog, Triage)   • Qdrant Vector Space    │
│   • Sovereign LLM-Dispatch (Ollama €0)        • SQLite FTS5 Index      │
│   • Code-Synthese & Ausführung                • Multi-User Isolation   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📣 4. Marketing- & Pitch-Skript (60 Sekunden)

> *„Stellen Sie sich vor, Ihr Unternehmen hätte das Gedächtnis und die Denkkraft aus der nordischen Mythologie.*
>
> *Wir installieren auf Ihren eigenen Servern **VIRKI** — Ihre persönliche, digitale Festung.*
>
> *Darin arbeiten zwei autonome Raben für Sie:*
> - ***Muninn*** *fliegt durch Ihre Mails, Chats, Dokumente und Meetings. Er speichert das gesamte Wissen Ihrer Firma, damit nie wieder wertvolles Wissen verloren geht.*
> - ***Huginn*** *ist Ihre denkende KI-Engine. Er nimmt dieses Wissen und erledigt automatisch Ihre Recherchen, Berichte, Code-Analysen und Auswertungen.*
>
> *Sie selbst müssen nicht mehr im Datenchaos suchen. Sie sitzen entspannt auf dem Regie-Stuhl und treffen mit 100 % Klarheit Ihre Entscheidungen.*
>
> ***VIRKI: Ein System. Zwei Raben. Volle Souveränität.“***
