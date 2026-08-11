import { UnifiedSearch } from "@/components/UnifiedSearch";

export const dynamic = "force-dynamic";

export default function SearchPage() {
  return (
    <section className="rise pt-10">
      <div className="mb-8">
        <h1 className="section-title">Knowledge Finder & Suche</h1>
        <p className="muted m-0 max-w-2xl">
          Der globale Dokumenten- & Vektor-Index: Durchsucht den Knowledge Graph, freigegebene Dokumente,
          Rohdateien (<span className="mono">Projekte/active/</span>) und Cursor-Chat-Protokolle mit direkter KI-Zusammenfassung und Quellen-Badges.
        </p>
      </div>
      <UnifiedSearch />
    </section>
  );
}
