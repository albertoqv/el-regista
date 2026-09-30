import type { Twin, TwinProfile } from "@/lib/api";
import { formatAge, formatMarketValue } from "@/lib/format";

export type Saving =
  | { kind: "cheaper"; amount: number; share: number }
  | { kind: "pricier"; amount: number }
  | { kind: "unknown" };

export function saving(target: TwinProfile, twin: Twin): Saving {
  if (target.market_value_eur === null || twin.market_value_eur === null) {
    return { kind: "unknown" };
  }
  const difference = target.market_value_eur - twin.market_value_eur;
  if (difference > 0) {
    return {
      kind: "cheaper",
      amount: difference,
      share: Math.round((difference / target.market_value_eur) * 100),
    };
  }
  return { kind: "pricier", amount: -difference };
}

export function savingLabel(value: Saving): string | null {
  if (value.kind === "cheaper") {
    return `Te ahorras ${formatMarketValue(value.amount)} (−${value.share}%)`;
  }
  if (value.kind === "pricier") {
    return value.amount === 0 ? "Mismo precio" : `${formatMarketValue(value.amount)} más caro`;
  }
  return null;
}

export type TwinBadge = { text: string; tone: "yellow" | "green" | "red" | "white" };

/** The stickers a scout would slap on the folder. */
export function badges(target: TwinProfile, twin: Twin): TwinBadge[] {
  const result: TwinBadge[] = [];
  const value = saving(target, twin);
  if (twin.similarity >= 92) result.push({ text: "Casi un clon", tone: "white" });
  if (value.kind === "cheaper" && value.share >= 70 && twin.similarity >= 80) {
    result.push({ text: "¡Ganga!", tone: "yellow" });
  }
  const targetAge = Number(formatAge(target)?.replace("~", ""));
  const twinAge = Number(formatAge(twin)?.replace("~", ""));
  if (targetAge && twinAge && twinAge <= 21 && twinAge < targetAge + 3) {
    result.push({ text: "Joven", tone: "green" });
  }
  return result.slice(0, 2);
}

export const BUDGETS: { value: number | null; label: string }[] = [
  { value: null, label: "Sin límite" },
  { value: 100_000_000, label: "≤ 100M" },
  { value: 50_000_000, label: "≤ 50M" },
  { value: 30_000_000, label: "≤ 30M" },
  { value: 15_000_000, label: "≤ 15M" },
  { value: 5_000_000, label: "≤ 5M" },
];

export const AGES: { value: number | null; label: string }[] = [
  { value: null, label: "Cualquier edad" },
  { value: 21, label: "Sub-21" },
  { value: 23, label: "Sub-23" },
  { value: 25, label: "≤ 25" },
  { value: 28, label: "≤ 28" },
];
