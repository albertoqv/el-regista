---
paths:
  - "web/**"
---

# Web (Next.js)

- Next.js 16 (App Router), Tailwind. Lee `web/AGENTS.md`: hay APIs cambiadas respecto
  a lo conocido.
- **Marca El Regista** (tema claro, `color-scheme: only light`): papel #F7F6F2, tinta
  #16171B, naranja balón #C93C17 (acento y Scout) y azul #2350D8 (Pronósticos, oculto;
  jugador/local A). Los tokens están en `globals.css`.
- Prohibido: verde+amarillo (casa de apuestas), granate, iconos en menús, puntitos de
  color, rótulos pequeños en mayúsculas espaciadas y efectos "de IA" (notas manuscritas,
  brillos, degradados, cristal). Poco texto; mínimo 13 px (`--text-xs`).
- Tipografía: **Regista Display** propia (solo mayúsculas) para titulares ≥3xl y cifras;
  **Schibsted Grotesk** (`font-heading`, negrita) para títulos pequeños, menús y texto.
  Texto sobre fotos: `photo-header`/`on-photo` (lo fuerza a claro); un buscador dentro de
  una foto lleva `on-paper`.
- Logo, iconos y fuente se generan con `scripts/brand/*.py` (shapely + fontTools) →
  `web/app/fonts/`, `web/public/brand/`, `web/app/components/icons.tsx` (no editar a mano).
- Fotos libres en `web/public/photos` con créditos en `lib/photos.ts` (pie de página);
  fotos grandes de jugador vía `bigPhoto()` (Transfermarkt `/portrait/big/`).
- Métricas y textos explicativos en `web/lib/metrics.ts`. `web/lib/products.ts` es la
  fuente única de menú, pestañas, portada y pie: solo se ven los `VISIBLE_PRODUCTS`
  (Pronósticos lleva `hidden`; sus páginas tienen `noindex` en su `layout.tsx`).
- Animaciones con `motion` (`motion/react`), pero **no en componentes de la portada**:
  allí son CSS (`rise-in`, `grow-x`, `dropdown-in`) y `Reveal` es de servidor y nunca
  oculta contenido sin JS.
- El menú móvil va fuera del `<header>` (su backdrop-blur recorta hijos `fixed`).
- CSP en `next.config.ts`: cualquier origen externo nuevo hay que añadirlo ahí; el e2e
  falla con cualquier error de consola.
- Horas de partido: Understat da UTC, la web las muestra en Europe/Madrid.
- Trampas: SVG calculado en servidor → redondear coordenadas (hidratación); `<title>` de
  SVG con un único string; headless Chrome en Windows no baja de ~500 px de ancho; el
  `overflow: clip` del body esconde el scroll horizontal (medir `scrollX` real).
- Comprobar: `cd web && npx tsc --noEmit && npm run lint && npm run build`.
