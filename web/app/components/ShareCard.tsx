"use client";

import { useState } from "react";

/** Shares a card image (native share sheet on phones, download elsewhere). */
export function ShareCard({
  playerId,
  name,
  imageUrl,
  shareText,
  label = "Compartir carta",
}: {
  playerId?: number;
  name: string;
  imageUrl?: string;
  shareText?: string;
  label?: string;
}) {
  const [busy, setBusy] = useState(false);
  const url = imageUrl ?? `/players/${playerId}/card`;
  const fileName = `${name.replace(/\s+/g, "-").toLowerCase()}-elregista.png`;

  async function share() {
    setBusy(true);
    try {
      const blob = await (await fetch(url)).blob();
      const file = new File([blob], fileName, { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: `${name} · El Regista`,
          text: shareText ?? `Mira el perfil de ${name} en El Regista`,
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
      {busy ? "Preparando imagen…" : label}
    </button>
  );
}
