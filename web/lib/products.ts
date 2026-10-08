export type ProductIcon =
  | "search"
  | "filter"
  | "twins"
  | "scale"
  | "flame"
  | "calendar"
  | "checks"
  | "shield"
  | "trophy";

export type ProductTool = {
  href: string;
  label: string;
  description: string;
  icon: ProductIcon;
  /** Other paths that belong to this tool (e.g. player pages to "Buscar"). */
  also?: string[];
};

export type Product = {
  key: "scout" | "pronosticos";
  name: string;
  subject: string;
  pitch: string;
  color: string;
  tools: ProductTool[];
  /** Still reachable by link, but out of the menu, home page, footer and sitemap. */
  hidden?: boolean;
};

/** The two products of El Regista: one about players, one about matches (hidden). */
export const PRODUCTS: Product[] = [
  {
    key: "scout",
    name: "Scout",
    subject: "Jugadores",
    pitch: "Encuentra, compara y ficha jugadores con datos reales de 33 ligas.",
    color: "#c93c17",
    tools: [
      {
        href: "/buscar",
        label: "Buscar jugador",
        description: "Ficha completa: radar, tiros, valor y evolución.",
        icon: "search",
        also: ["/players"],
      },
      {
        href: "/explorar",
        label: "Explorador",
        description: "Filtra por liga, edad, precio y cualquier métrica.",
        icon: "filter",
      },
      {
        href: "/gemelos",
        label: "Gemelos",
        description: "El mismo estilo de juego, por menos dinero.",
        icon: "twins",
      },
      {
        href: "/compare",
        label: "Comparar",
        description: "Cara a cara con percentiles y veredicto.",
        icon: "scale",
      },
      {
        href: "/ranking",
        label: "Rankings",
        description: "Goleadores, asistentes y xG de cada liga.",
        icon: "trophy",
      },
      {
        href: "/en-racha",
        label: "En racha",
        description: "Quién está en forma en las últimas semanas.",
        icon: "flame",
      },
      {
        href: "/infravalorados",
        label: "Infravalorados",
        description: "Rinden como si valieran más que su precio.",
        icon: "scale",
      },
    ],
  },
  {
    key: "pronosticos",
    name: "Pronósticos",
    subject: "Partidos",
    pitch: "Probabilidades de cada partido y un historial de aciertos que no se puede maquillar.",
    color: "#2350d8",
    hidden: true,
    tools: [
      {
        href: "/predicciones",
        label: "Próximos partidos",
        description: "Resultado, goles, córners, tarjetas y goleadores.",
        icon: "calendar",
      },
      {
        href: "/predicciones/historial",
        label: "Historial de aciertos",
        description: "Lo que predijimos antes del partido, contra lo que pasó.",
        icon: "checks",
      },
      {
        href: "/equipos",
        label: "Equipos",
        description: "Clasificación real, por xG y estilo de cada equipo.",
        icon: "shield",
      },
    ],
  },
];

/** What the menu, home page and footer show. */
export const VISIBLE_PRODUCTS = PRODUCTS.filter((product) => !product.hidden);

function matches(pathname: string, path: string): boolean {
  return pathname === path || pathname.startsWith(`${path}/`);
}

/** The product and tool a path belongs to (the most specific tool wins). */
export function locate(pathname: string): { product: Product; tool: ProductTool } | null {
  let best: { product: Product; tool: ProductTool; length: number } | null = null;
  for (const product of PRODUCTS) {
    for (const tool of product.tools) {
      for (const path of [tool.href, ...(tool.also ?? [])]) {
        if (matches(pathname, path) && (!best || path.length > best.length)) {
          best = { product, tool, length: path.length };
        }
      }
    }
  }
  return best ? { product: best.product, tool: best.tool } : null;
}
