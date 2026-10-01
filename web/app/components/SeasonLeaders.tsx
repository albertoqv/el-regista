"use client";

import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useRef, useState } from "react";
import { Avatar } from "@/app/components/Avatar";
import { CountUp } from "@/app/components/motion";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { listSeasonLeaders, type LeaderMetric, type SeasonLeader } from "@/lib/api";
import {
  COMPETITIONS,
  competitionColor,
  positionShort,
  seasonDisplay,
} from "@/lib/format";
import { LEADER_TABS, METRICS } from "@/lib/metrics";

const LIMIT = 10;
const PODIUM_ORDER = [1, 0, 2];
const MEDALS = ["#f5c451", "#cfd6e4", "#e0935a"];

function valueOf(leader: SeasonLeader, metric: LeaderMetric): number {
  return leader[metric];
}

function decimalsOf(metric: LeaderMetric): number {
  return METRICS[metric].decimals ?? 0;
}

function PodiumCard({
  leader,
  rank,
  metric,
}: {
  leader: SeasonLeader;
  rank: number;
  metric: LeaderMetric;
}) {
  const first = rank === 0;
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, delay: first ? 0 : 0.1 + rank * 0.08 }}
      className={first ? "sm:-mt-6" : "sm:mt-6"}
    >
      <Link
        href={`/players/${leader.player_id}`}
        className="group relative block"
      >
        <PlayerPortrait
          name={leader.name}
          photoUrl={leader.photo_url}
          accent={MEDALS[rank]}
          className={`w-full transition duration-500 group-hover:-translate-y-1 ${first ? "aspect-[3/4]" : "aspect-[3/4] sm:aspect-[4/5]"}`}
        />
        <div
          className="absolute left-3 top-3 flex h-9 w-9 items-center justify-center rounded-full font-display text-lg font-bold text-bg"
          style={{ background: MEDALS[rank] }}
        >
          {rank + 1}
        </div>
        <div className="absolute inset-x-0 bottom-0 flex flex-col gap-0.5 p-4">
          <span className="font-display text-4xl font-bold leading-none tabular-nums sm:text-6xl">
            <CountUp value={valueOf(leader, metric)} decimals={decimalsOf(metric)} />
          </span>
          <span className="truncate font-display text-sm font-semibold sm:text-xl">
            {leader.name}
          </span>
          <span className="flex items-center gap-1.5 truncate text-xs text-muted">
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ background: competitionColor(leader.competition) }}
            />
            {leader.team ?? leader.competition}
          </span>
        </div>
      </Link>
    </motion.div>
  );
}

export function SeasonLeaders({
  startYear,
  initialLeaders,
}: {
  startYear: number;
  initialLeaders: SeasonLeader[];
}) {
  const [metric, setMetric] = useState<LeaderMetric>("goals");
  const [competition, setCompetition] = useState<string | null>(null);
  const [leaders, setLeaders] = useState(initialLeaders);
  const [loading, setLoading] = useState(false);
  const request = useRef(0);

  function load(nextMetric: LeaderMetric, nextCompetition: string | null) {
    setMetric(nextMetric);
    setCompetition(nextCompetition);
    setLoading(true);
    const id = ++request.current;
    listSeasonLeaders(startYear, {
      metric: nextMetric,
      limit: LIMIT,
      competition: nextCompetition ?? undefined,
    })
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

  const podium = leaders.slice(0, 3);
  const rest = leaders.slice(3);
  const maxValue = Math.max(...leaders.map((leader) => valueOf(leader, metric)), 1);
  const info = METRICS[metric];

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-brand-2">
            Temporada {seasonDisplay(String(startYear))} · en directo
          </p>
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Los mejores en <span className="text-gradient">{info.short}</span>
          </h2>
        </div>
      </div>

      <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
        {LEADER_TABS.map((tab) => (
          <button
            key={tab.metric}
            type="button"
            onClick={() => load(tab.metric, competition)}
            className={`relative shrink-0 rounded-full px-4 py-2 text-sm font-medium transition ${metric === tab.metric ? "text-bg" : "text-muted hover:text-ink"}`}
          >
            {metric === tab.metric && (
              <motion.span
                layoutId="leader-tab"
                className="absolute inset-0 rounded-full bg-brand"
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
              />
            )}
            <span className="relative">{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:px-0">
        {[null, ...COMPETITIONS].map((option) => {
          const active = competition === option;
          const color = option ? competitionColor(option) : "#7cc0ff";
          return (
            <button
              key={option ?? "all"}
              type="button"
              onClick={() => load(metric, option)}
              className="flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition"
              style={{
                borderColor: active ? color : "rgba(255,255,255,0.08)",
                background: active ? `${color}22` : "transparent",
                color: active ? "#fff" : "#8b93a7",
              }}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
              {option ?? "Las 5 ligas"}
            </button>
          );
        })}
      </div>

      <div className={`transition-opacity duration-300 ${loading ? "opacity-40" : "opacity-100"}`}>
        {leaders.length === 0 ? (
          <p className="glass rounded-lg p-8 text-center text-sm text-muted">
            Todavía no hay datos de esta temporada.
          </p>
        ) : (
          <div className="flex flex-col gap-6">
            <div className="mx-auto grid w-full max-w-4xl grid-cols-3 items-end gap-3 pt-6 sm:gap-6">
              <AnimatePresence mode="popLayout">
                {PODIUM_ORDER.filter((rank) => podium[rank]).map((rank) => (
                  <PodiumCard
                    key={`${metric}-${competition}-${podium[rank].player_id}`}
                    leader={podium[rank]}
                    rank={rank}
                    metric={metric}
                  />
                ))}
              </AnimatePresence>
            </div>

            <ol className="glass grid grid-cols-1 gap-1 rounded-lg p-3 md:grid-cols-2 md:gap-x-4">
              {rest.map((leader, index) => {
                const value = valueOf(leader, metric);
                return (
                  <motion.li
                    key={`${metric}-${competition}-${leader.player_id}`}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 + index * 0.05 }}
                  >
                    <Link
                      href={`/players/${leader.player_id}`}
                      className="relative flex items-center gap-3 overflow-hidden rounded-lg px-3 py-2.5 transition hover:bg-white/5"
                    >
                      <motion.span
                        className="absolute inset-y-1 left-0 rounded-lg bg-surface-strong"
                        initial={{ width: 0 }}
                        animate={{ width: `${(value / maxValue) * 100}%` }}
                        transition={{ duration: 0.8, delay: 0.3 + index * 0.05 }}
                      />
                      <span className="relative w-5 text-center font-display text-sm font-bold text-muted">
                        {index + 4}
                      </span>
                      <span className="relative">
                        <Avatar name={leader.name} photoUrl={leader.photo_url} size={38} />
                      </span>
                      <span className="relative flex min-w-0 flex-1 flex-col">
                        <span className="truncate text-sm font-semibold">{leader.name}</span>
                        <span className="flex items-center gap-1.5 truncate text-xs text-muted">
                          <span
                            className="h-1.5 w-1.5 shrink-0 rounded-full"
                            style={{ background: competitionColor(leader.competition) }}
                          />
                          {leader.team ?? leader.competition} · {positionShort(leader.position)}
                        </span>
                      </span>
                      <span className="relative font-display text-xl font-bold tabular-nums">
                        {value.toLocaleString("es-ES", {
                          minimumFractionDigits: decimalsOf(metric),
                          maximumFractionDigits: decimalsOf(metric),
                        })}
                      </span>
                    </Link>
                  </motion.li>
                );
              })}
            </ol>
          </div>
        )}
      </div>
    </section>
  );
}
