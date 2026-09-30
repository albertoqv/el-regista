import {
  IconCalendar,
  IconChecks,
  IconDefense,
  IconFilter,
  IconFlame,
  IconScale,
  IconSearch,
  IconTwins,
} from "@/app/components/icons";
import type { ProductIcon as ProductIconName } from "@/lib/products";

const ICONS = {
  search: IconSearch,
  filter: IconFilter,
  twins: IconTwins,
  scale: IconScale,
  flame: IconFlame,
  calendar: IconCalendar,
  checks: IconChecks,
  shield: IconDefense,
} as const;

export function ProductIcon({
  name,
  size = 18,
  color,
}: {
  name: ProductIconName;
  size?: number;
  color?: string;
}) {
  const Icon = ICONS[name];
  return <Icon size={size} color={color} />;
}
