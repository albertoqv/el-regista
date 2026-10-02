/* eslint-disable @next/next/no-img-element */
import { ImageResponse } from "next/og";
import { COVER_PHOTO, LOGO_DARK, LOGO_RATIO, OG_COLORS, OG_FONTS } from "@/lib/og-brand";

export const alt = "El Regista: scout y pronósticos de fútbol con datos reales";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** The picture shown when the site is shared on WhatsApp, X, Facebook or LinkedIn. */
export default function Image() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", position: "relative", fontFamily: "Regista", color: OG_COLORS.chalk }}>
        <img src={COVER_PHOTO} width={1200} height={630} style={{ position: "absolute", top: 0, left: 0, objectFit: "cover" }} alt="" />
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: 1200,
            height: 630,
            display: "flex",
            backgroundImage: "linear-gradient(90deg, rgba(15,16,19,0.97) 0%, rgba(15,16,19,0.88) 55%, rgba(15,16,19,0.35) 100%)",
          }}
        />
        <div style={{ position: "relative", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 70, width: "100%" }}>
          <img src={LOGO_DARK} height={70} width={Math.round(70 * LOGO_RATIO)} alt="" />
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div style={{ display: "flex", fontSize: 96, lineHeight: 0.92 }}>FÚTBOL CON</div>
            <div style={{ display: "flex", fontSize: 96, lineHeight: 0.92 }}>DATOS DE VERDAD</div>
            <div style={{ display: "flex", gap: 16, marginTop: 18, fontSize: 32 }}>
              <span style={{ display: "flex", background: OG_COLORS.yellow, color: OG_COLORS.slate, padding: "6px 16px" }}>SCOUT</span>
              <span style={{ display: "flex", background: "#5b8cff", color: OG_COLORS.slate, padding: "6px 16px" }}>PRONÓSTICOS</span>
            </div>
          </div>
        </div>
      </div>
    ),
    { ...size, fonts: OG_FONTS },
  );
}
