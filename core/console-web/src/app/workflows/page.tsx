"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function WorkflowsPageRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/workflows/research");
  }, [router]);

  return (
    <div className="p-12 text-center text-slate-400 font-mono text-xs animate-pulse">
      Leite zum Agenten Cockpit (/agents) weiter...
    </div>
  );
}
