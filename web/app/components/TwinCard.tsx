import Link from "next/link";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { Sticker } from "@/app/components/ScoutNote";
import type { Twin, TwinProfile } from "@/lib/api";
import {
  competitionColor,
  formatAge,
  formatMarketValue,
  roleLabel,
  seasonDisplay,
} from "@/lib/format";
import { PROFILE_LABELS } from "@/lib/metrics";
import { MiniRadar } from "@/app/components/MiniRadar";
import { badges, saving, savingLabel } from "@/lib/twins";

function compareHref(target: TwinProfile, twin: Twin): string {
  return `/compare?${new URLSearchParams({
    a: String(target.player_id),
    b: String(twin.player_id),
    sac: target.competition,
    sal: target.season_label,
    sbc: twin.competition,
    sbl: twin.season_label,
  }).toString()}`;
}

function metricName(key: string): string {
  return PROFILE_LABELS[key] ?? key;
}

export function TwinCard({
  target,
  twin,
  rank,
}: {
  target: TwinProfile;
  twin: Twin;
  rank: number;
}) {
  const value = saving(target, twin);
  const label = savingLabel(value);
  const age = formatAge(twin);
  const tilt = rank % 2 === 0 ? -3 : 3;

  return (
    <article className="glass glass-hover group relative flex h-full flex-col overflow-hidden rounded-lg">
      <div className="relative">
        <PlayerPortrait
          name={twin.name}
          photoUrl={twin.photo_url}
          accent={competitionColor(twin.competition)}
          rounded="rounded-none"
          focus="center 28%"
          className="aspect-[4/3] w-full"
        />
        <div className="absolute left-3 top-3 flex flex-col items-start gap-1.5">
          {badges(target, twin).map((badge, index) => (
            <Sticker key={badge.text} tone={badge.tone} rotate={tilt + index * 2}>
              {badge.text}
            </Sticker>
          ))}
        </div>
        <div className="absolute right-3 top-3 flex h-14 w-14 flex-col items-center justify-center rounded-full border border-ink/15 bg-black/65">
          <span className="font-heading text-lg leading-none">{twin.similarity}%</span>
          <span className="text-[8px] font-semibold text-muted">igual</span>
        </div>
        <div className="absolute inset-x-0 bottom-0 p-4">
          <h3 className="font-heading text-xl leading-tight">{twin.name}</h3>
          <p className="flex items-center gap-1.5 text-xs text-ink/75">
            {twin.team ?? twin.competition} · {seasonDisplay(twin.season_label)}
            {twin.detailed_position && ` · ${roleLabel(twin)}`}
            {age && ` · ${age} años`}
          </p>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-end justify-between gap-2">
          <div>
            <span className="block text-xs font-semibold text-muted">
              Valor
            </span>
            <span className="font-heading text-2xl">
              {twin.market_value_eur !== null ? formatMarketValue(twin.market_value_eur) : "—"}
            </span>
          </div>
          {label && (
            <span
              className={`rounded-lg px-2 py-1 text-right text-xs font-semibold ${value.kind === "cheaper" ? "bg-grass/12 text-brand-2" : "bg-ink/5 text-muted"}`}
            >
              {label}
            </span>
          )}
          {value.kind === "unknown" && twin.market_value_eur === null && (
            <span className="text-right text-xs text-muted">precio aún sin cargar</span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <MiniRadar target={target.percentiles} twin={twin.percentiles} />
          <div className="flex flex-col gap-1.5">
            {twin.shared_strengths.length > 0 && (
              <p className="text-sm text-ink/85">
                <span className="text-muted">Se parecen en </span>
                {twin.shared_strengths.map(metricName).join(", ")}
              </p>
            )}
            {twin.differences.length > 0 && (
              <p className="text-xs text-muted">
                Donde cambia: {twin.differences.map(metricName).join(", ")}
              </p>
            )}
          </div>
        </div>

        <div className="mt-auto flex gap-2 pt-1">
          <Link
            href={compareHref(target, twin)}
            className="flex-1 rounded-full bg-ink px-3 py-2 text-center text-xs font-bold text-bg transition hover:bg-ink/85"
          >
            Cara a cara
          </Link>
          <Link
            href={`/gemelos?p=${twin.player_id}`}
            className="rounded-full border border-line px-3 py-2 text-xs font-semibold text-ink/80 transition hover:border-line-strong"
            title={`Buscar gemelos de ${twin.name}`}
          >
            Sus gemelos
          </Link>
        </div>
      </div>
    </article>
  );
}
