import { readFile } from "node:fs/promises";
import { join } from "node:path";

// Brand assets for the share images (next/og). Read once per server instance.
const [font, logo] = await Promise.all([
  readFile(join(process.cwd(), "app/fonts/RegistaDisplay.ttf")),
  readFile(join(process.cwd(), "public/brand/logo-dark.svg")),
]);

export const LOGO_DARK = `data:image/svg+xml;base64,${logo.toString("base64")}`;
export const LOGO_RATIO = 5.25;

export const OG_FONTS = [
  { name: "Regista", data: font, style: "normal" as const, weight: 400 as const },
];

export const OG_COLORS = {
  slate: "#1f3b2d",
  deep: "#173024",
  chalk: "#f2efe6",
  dim: "#b9c4b8",
  yellow: "#f2c230",
  grass: "#9ed7b3",
};
