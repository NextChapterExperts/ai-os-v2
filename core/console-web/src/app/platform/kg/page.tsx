import { Suspense } from "react";
import { KnowledgeGraphBrowser } from "@/components/KnowledgeGraphBrowser";

export default function KnowledgeGraphPage() {
  return (
    <Suspense fallback={<p className="muted">Graph lädt…</p>}>
      <KnowledgeGraphBrowser />
    </Suspense>
  );
}
