"use client";

import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useRef, useState } from "react";
import { Avatar } from "@/app/components/Avatar";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { ScoutNote } from "@/app/components/ScoutNote";
import { listShotLeaders, type ShotLeader, type ShotMetric } from "@/lib/api";
import { seasonDisplay } from "@/lib/format";
import { SHOT_METRICS } from "@/lib/shots";

function format(value: number, metric: ShotMetric, decimals: number): string {
  const text = value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return metric === "finishing" && value > 0 ? `+${text}` : text;
}

/** Wyscout-style situational rankings built from every shot of the season. */
export function SeasonMoments({
  startYear,
  initialLeaders,
}: {
  startYear: number;
  initialLeaders: ShotLeader[];
}) {
  const [metric, setMetric] = useState<ShotMetric>("late_goals");
  const [leaders, setLeaders] = useState(initialLeaders);
  const [loading, setLoading] = useState(false);
  const request = useRef(0);
  const info = SHOT_METRICS.find((entry) => entry.metric === metric) ?? SHOT_METRICS[0];

  function load(next: ShotMetric) {
    setMetric(next);
    setLoading(true);
    const id = ++request.current;
    listShotLeaders(startYear, { metric: next, limit: 8 })
      .then((result) => {
        if (id === request.current) setLeaders(result);
      })
      .catch(() => {
        if (id === request.current) setLeaders([]);
      })
      .finally(() => {
        if (id === request.current) setLoading(false);
      });
  }

  const [first, ...rest] = leaders;

  return (
    <section className="flex flex-col gap-6">
      <div>
        <ScoutNote rotate={-2}>lo que no sale en la tele</ScoutNote>
        <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
          Momentos de la temporada {seasonDisplay(String(startYear))}
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Sacado de cada tiro de cada partido: cuándo, desde dónde, con qué y si sirvió para algo.
        </p>
      </div>

      <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
        {SHOT_METRICS.map((entry) => (
          <button
            key={entry.metric}
            type="button"
            onClick={() => load(entry.metric)}
            className={`shrink-0 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
              metric === entry.metric
                ? "border-[#c93c17] bg-[#c93c17] text-bg"
                : "border-line text-muted hover:border-line-strong hover:text-ink"
            }`}
          >
            {entry.label}
          </button>
        ))}
      </div>

      <div className={`transition-opacity duration-300 ${loading ? "opacity-40" : ""}`}>
        {!first ? (
          <p className="glass rounded-lg p-8 text-center text-sm text-muted">
            Aún no hay tiros cargados de esta temporada.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[320px_1fr]">
            <AnimatePresence mode="wait">
              <motion.div
                key={`${metric}-${first.player_id}`}
                initial={{ opacity: 0, rotate: -4, y: 20 }}
                animate={{ opacity: 1, rotate: -1.5, y: 0 }}
                exit={{ opacity: 0, rotate: 3, y: -10 }}
                transition={{ type: "spring", stiffness: 160, damping: 18 }}
              >
                <Link href={`/players/${first.player_id}`} className="group relative block">
                  <PlayerPortrait
                    name={first.name}
                    photoUrl={first.photo_url}
                    accent="#c93c17"
                    className="aspect-[4/5] w-full"
                  />
                  <div className="absolute inset-x-0 bottom-0 p-5">
                    <p className="text-xs font-semibold text-[#c93c17]">
                      {info.title}
                    </p>
                    <p className="font-display text-6xl font-bold leading-none">
                      {format(first.value, metric, info.decimals)}
                    </p>
                    <p className="text-xs text-muted">{info.unit}</p>
                    <p className="mt-1 font-heading text-xl">{first.name}</p>
                    <p className="text-xs text-muted">{first.team ?? first.competition}</p>
                  </div>
                </Link>
              </motion.div>
            </AnimatePresence>

            <div className="glass flex flex-col rounded-lg p-3">
              <p className="px-3 pb-2 pt-1 text-sm text-muted">{info.help}</p>
              <ol className="flex flex-col gap-1">
                {rest.map((leader, index) => (
                  <motion.li
                    key={`${metric}-${leader.player_id}`}
                    initial={{ opacity: 0, x: 16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.04 }}
                  >
                    <Link
                      href={`/players/${leader.player_id}`}
                      className="flex items-center gap-3 rounded-lg px-3 py-2 transition hover:bg-ink/5"
                    >
                      <span className="w-5 text-center font-heading text-sm text-muted">
                        {index + 2}
                      </span>
                      <Avatar name={leader.name} photoUrl={leader.photo_url} size={36} />
                      <span className="flex min-w-0 flex-1 flex-col">
                        <span className="truncate text-sm font-semibold">{leader.name}</span>
                        <span className="flex items-center gap-1.5 truncate text-xs text-muted">
                          {leader.team ?? leader.competition}
                        </span>
                      </span>
                      <span className="font-display text-xl font-bold tabular-nums">
                        {format(leader.value, metric, info.decimals)}
                      </span>
                    </Link>
                  </motion.li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
