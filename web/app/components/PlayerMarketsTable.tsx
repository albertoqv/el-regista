"use client";

import Link from "next/link";
import { useState } from "react";
import { Avatar } from "@/app/components/Avatar";
import type { PlayerMarket, PlayerMarkets } from "@/lib/api";

const MARKETS: { key: keyof PlayerMarket; label: string; help: string }[] = [
  { key: "goal", label: "Marca", help: "Probabilidad de marcar al menos un gol." },
  { key: "assist", label: "Asiste", help: "Probabilidad de dar al menos una asistencia." },
  { key: "card", label: "Amarilla", help: "Probabilidad de ver tarjeta amarilla." },
  { key: "shots_2", label: "2+ tiros", help: "Probabilidad de hacer dos disparos o más." },
];

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function Column({
  team,
  players,
  market,
  color,
}: {
  team: string;
  players: PlayerMarket[];
  market: keyof PlayerMarket;
  color: string;
}) {
  const sorted = [...players].sort((a, b) => (b[market] as number) - (a[market] as number)).slice(0, 8);
  const max = Math.max(...sorted.map((p) => p[market] as number), 0.01);
  return (
    <div className="flex flex-col gap-2">
      <h4 className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color }}>
        {team}
      </h4>
      <ol className="flex flex-col gap-1.5">
        {sorted.map((player) => {
          const value = player[market] as number;
          const content = (
            <span className="relative flex items-center gap-3 overflow-hidden rounded-xl px-2 py-1.5">
              <span
                className="absolute inset-y-0 left-0 rounded-xl opacity-20"
                style={{ width: `${(value / max) * 100}%`, background: color }}
              />
              <span className="relative">
                <Avatar name={player.name} photoUrl={player.photo_url} size={30} />
              </span>
              <span className="relative flex min-w-0 flex-1 flex-col">
                <span className="truncate text-sm font-semibold">{player.name}</span>
                <span className="text-[10px] text-muted">
                  {player.position} · ~{Math.round(player.expected_minutes)}&apos;
                </span>
              </span>
              <span className="relative font-display text-lg font-bold tabular-nums">{percent(value)}</span>
            </span>
          );
          return (
            <li key={player.understat_player_id}>
              {player.player_id ? (
                <Link href={`/players/${player.player_id}`} className="block hover:bg-white/5 rounded-xl">
                  {content}
                </Link>
              ) : (
                content
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export function PlayerMarketsTable({ markets }: { markets: PlayerMarkets }) {
  const [market, setMarket] = useState<keyof PlayerMarket>("goal");
  const info = MARKETS.find((entry) => entry.key === market) ?? MARKETS[0];
  return (
    <section className="glass flex flex-col gap-4 rounded-3xl p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-bold tracking-tight">Jugadores</h2>
          <p className="text-sm text-muted">{info.help} Minutos esperados según sus últimos partidos.</p>
        </div>
        <div className="glass flex rounded-full p-1 text-xs font-semibold">
          {MARKETS.map((entry) => (
            <button
              key={entry.key}
              type="button"
              onClick={() => setMarket(entry.key)}
              className={`rounded-full px-3 py-1.5 transition ${market === entry.key ? "bg-white text-black" : "text-muted hover:text-ink"}`}
            >
              {entry.label}
            </button>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Column team={markets.home_team} players={markets.home} market={market} color="#3d8bff" />
        <Column team={markets.away_team} players={markets.away} market={market} color="#ff6b3d" />
      </div>
    </section>
  );
}
