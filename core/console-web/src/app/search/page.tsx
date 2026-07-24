import { UnifiedSearch } from "@/components/UnifiedSearch";

export const dynamic = "force-dynamic";

export default function SearchPage() {
  return (
    <section className="rise pt-10">
      <div className="mb-8">
        <h1 className="section-title">Suche</h1>
        <p className="muted m-0 max-w-xl">
          Durchsucht das freigegebene Company Brain und die rohen Projektdateien
          (<span className="mono">Projekte/active/</span>) gemeinsam — klar markiert, was
          kuratiert und was ungeprüft ist.
        </p>
      </div>
      <UnifiedSearch />
    </section>
  );
}
