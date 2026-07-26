"use client";

import { useEffect, useState } from "react";

export type OrgPersonItem = {
  id: string;
  name: string;
  email?: string;
  role?: string;
};

export function UserSelector() {
  const [people, setPeople] = useState<OrgPersonItem[]>([
    {
      id: "person:peter-alexander",
      name: "Peter Alexander",
      email: "peter.alexander@nextchapterexperts.de",
      role: "Founder / Operator",
    },
  ]);
  const [selectedUser, setSelectedUser] = useState<string>("person:peter-alexander");

  useEffect(() => {
    // Restore from localStorage
    const saved = localStorage.getItem("aios_active_user_id");
    if (saved) {
      setSelectedUser(saved);
    }

    // Fetch people from API
    fetch("/api/people")
      .then((res) => res.json())
      .then((data) => {
        if (data?.people && Array.isArray(data.people) && data.people.length > 0) {
          setPeople(data.people);
          if (!saved) {
            setSelectedUser(data.people[0].id);
            localStorage.setItem("aios_active_user_id", data.people[0].id);
          }
        }
      })
      .catch(() => {
        // Fallback already initialized
      });
  }, []);

  const handleChange = (newId: string) => {
    setSelectedUser(newId);
    localStorage.setItem("aios_active_user_id", newId);
    const person = people.find((p) => p.id === newId);
    if (person) {
      localStorage.setItem("aios_active_user_name", person.name);
    }
    window.dispatchEvent(new CustomEvent("aios-user-changed", { detail: { userId: newId } }));
  };

  return (
    <div className="flex items-center gap-1.5 rounded-lg border border-line bg-surface-soft/60 px-2.5 py-1 text-xs">
      <span className="text-ink-soft">👤 User:</span>
      <select
        value={selectedUser}
        onChange={(e) => handleChange(e.target.value)}
        className="bg-transparent font-medium text-ink cursor-pointer outline-none hover:text-accent focus:text-accent"
        title="Aktiven Benutzer für Speicher & Suchen auswählen"
      >
        {people.map((p) => (
          <option key={p.id} value={p.id} className="bg-surface text-ink">
            {p.name} {p.role ? `(${p.role})` : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
