import { readFile } from "node:fs/promises";
import { join } from "node:path";

// Brand assets for the share images (next/og). Read once per server instance.
const [font, logo, cover] = await Promise.all([
  readFile(join(process.cwd(), "app/fonts/RegistaDisplay.ttf")),
  readFile(join(process.cwd(), "public/brand/logo-dark.svg")),
  readFile(join(process.cwd(), "public/photos/portada.jpg")),
]);

export const LOGO_DARK = `data:image/svg+xml;base64,${logo.toString("base64")}`;
export const LOGO_RATIO = 5.44;
export const COVER_PHOTO = `data:image/jpeg;base64,${cover.toString("base64")}`;

export const OG_FONTS = [
  { name: "Regista", data: font, style: "normal" as const, weight: 400 as const },
];

export const OG_COLORS = {
  slate: "#16171b",
  deep: "#0f1013",
  chalk: "#f7f6f2",
  dim: "#a9acb3",
  yellow: "#f2643a",
  grass: "#5b8cff",
};
