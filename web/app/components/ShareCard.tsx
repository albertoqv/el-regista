"use client";

import { useState } from "react";

/** Shares the player's card image (native share sheet on phones, download elsewhere). */
export function ShareCard({ playerId, name }: { playerId: number; name: string }) {
  const [busy, setBusy] = useState(false);
  const url = `/players/${playerId}/card`;
  const fileName = `${name.replace(/\s+/g, "-").toLowerCase()}-talentscope.png`;

  async function share() {
    setBusy(true);
    try {
      const blob = await (await fetch(url)).blob();
      const file = new File([blob], fileName, { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: `${name} · TalentScope`,
          text: `Mira el perfil de ${name} en TalentScope`,
        });
      } else {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        link.click();
        URL.revokeObjectURL(link.href);
      }
    } catch {
      // The user closed the share sheet: nothing to do.
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={share}
      disabled={busy}
      className="glass rounded-full px-5 py-2.5 text-sm font-semibold transition hover:border-line-strong disabled:opacity-60"
    >
      {busy ? "Preparando carta…" : "Compartir carta"}
    </button>
  );
}
