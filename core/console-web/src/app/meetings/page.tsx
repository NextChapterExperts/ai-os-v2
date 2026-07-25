import { MeetingsPanel } from "@/components/MeetingsPanel";

export const dynamic = "force-dynamic";

export default function MeetingsPage() {
  return (
    <section className="rise pt-6">
      <div className="mb-6">
        <h1 className="section-title m-0">Meetings</h1>
        <p className="muted mt-1 mb-0 max-w-2xl text-sm">
          Zentrale Meeting-Inbox — Launchpad, Kollegen, Planung: alles erfassen, Projekt-Zuordnung
          optional. Später: Calendar-Import und Graph-Sync.
        </p>
      </div>
      <MeetingsPanel />
    </section>
  );
}
