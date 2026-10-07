"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { SimilarityMeter } from "@/app/components/SimilarityMeter";
import type { MarketValuePoint, Player } from "@/lib/api";
import {
  footLabel,
  formatAge,
  formatMarketValue,
  positionLabel,
  seasonDisplay,
} from "@/lib/format";

export type FaceOffSide = {
  player: Player;
  context: string;
  marketValue: MarketValuePoint | null;
  /** The season compared, with the value and age the player had then. */
  then?: { label: string; value: MarketValuePoint | null; age: number | null } | null;
};

function Fighter({ side, color, fromLeft }: { side: FaceOffSide; color: string; fromLeft: boolean }) {
  const { player } = side;
  const age = formatAge(player);
  const then = side.then;
  const facts = [
    positionLabel(player.position),
    then?.age != null ? `${then.age} años en ${seasonDisplay(then.label)}` : null,
    age ? `${age} años hoy` : null,
    player.preferred_foot ? footLabel(player.preferred_foot) : null,
  ].filter(Boolean);

  return (
    <motion.div
      initial={{ opacity: 0, x: fromLeft ? -120 : 120, rotate: fromLeft ? -4 : 4 }}
      animate={{ opacity: 1, x: 0, rotate: 0 }}
      transition={{ type: "spring", stiffness: 70, damping: 14, delay: 0.1 }}
      className={`flex flex-col gap-3 ${fromLeft ? "items-start text-left" : "items-end text-right"}`}
    >
      <Link href={`/players/${player.player_id}`} className="group relative block w-full">
        <PlayerPortrait
          name={player.name}
          photoUrl={player.photo_url}
          accent={color}
          mirrored={!fromLeft}
          className="aspect-[3/4] w-full transition duration-500 group-hover:scale-[1.02]"
        />
        <div className={`absolute inset-x-0 bottom-0 flex flex-col p-4 sm:p-5 ${fromLeft ? "items-start" : "items-end"}`}>
          <span className="text-xs font-semibold" style={{ color }}>
            {side.context}
          </span>
          <span className="font-heading text-2xl leading-tight sm:text-4xl">{player.name}</span>
        </div>
      </Link>
      <div className={`flex flex-wrap gap-1.5 ${fromLeft ? "" : "justify-end"}`}>
        {facts.map((fact) => (
          <span key={fact} className="rounded-full bg-ink/5 px-2.5 py-1 text-xs text-ink/80">
            {fact}
          </span>
        ))}
        {then?.value && (
          <span className="rounded-full px-2.5 py-1 text-xs font-semibold" style={{ background: `${color}22`, color }}>
            {seasonDisplay(then.label)}: {formatMarketValue(then.value.amount_eur)}
          </span>
        )}
        {side.marketValue && (
          <span className="rounded-full px-2.5 py-1 text-xs font-semibold" style={{ background: `${color}22`, color }}>
            {then ? "Hoy: " : ""}
            {formatMarketValue(side.marketValue.amount_eur)}
          </span>
        )}
      </div>
    </motion.div>
  );
}

export function FaceOff({
  a,
  b,
  similarity,
}: {
  a: FaceOffSide;
  b: FaceOffSide;
  /** Null for a whole-season duel: no style metrics to compare. */
  similarity: number | null;
}) {
  return (
    <section className="relative -mx-4 overflow-x-clip px-4 py-2 sm:mx-0 sm:px-0">
      <div className="grid grid-cols-2 items-start gap-4 sm:gap-8 md:grid-cols-[1fr_auto_1fr]">
        <Fighter side={a} color="#2350d8" fromLeft />
        <motion.div
          initial={{ opacity: 0, scale: 0.4 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 160, damping: 12, delay: 0.55 }}
          className="order-last col-span-2 flex flex-col items-center gap-5 md:order-none md:col-span-1 md:pt-24"
        >
          <div className="relative flex h-20 w-20 items-center justify-center">
            <div className="relative flex h-16 w-16 items-center justify-center rounded-full border border-ink/20 bg-brand font-heading text-2xl text-bg">
              VS
            </div>
          </div>
          {similarity !== null && <SimilarityMeter percentage={similarity} size={140} />}
        </motion.div>
        <Fighter side={b} color="#c93c17" fromLeft={false} />
      </div>
    </section>
  );
}
