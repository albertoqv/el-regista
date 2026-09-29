import type { ReactNode } from "react";

const BRAND_COLOR = "#2a78d6";

type IconProps = {
  size?: number;
  className?: string;
  color?: string;
};

function IconBase({
  size = 20,
  className,
  color = BRAND_COLOR,
  children,
}: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

/** Ataque / goles: tendencia ascendente. */
export function IconAttack(props: IconProps) {
  return (
    <IconBase {...props}>
      <path d="M4 16l5-5 3.5 3.5L20 7" />
      <path d="M14.5 7H20v5.5" />
    </IconBase>
  );
}

/** Creación / asistencias: un pase que se reparte. */
export function IconCreate(props: IconProps) {
  return (
    <IconBase {...props}>
      <circle cx="6" cy="12" r="2.25" />
      <circle cx="18" cy="6" r="2.25" />
      <circle cx="18" cy="18" r="2.25" />
      <path d="M8 11l8-4M8 13l8 4" />
    </IconBase>
  );
}

/** Defensa: escudo. */
export function IconDefense(props: IconProps) {
  return (
    <IconBase {...props}>
      <path d="M12 3.5l7 2.5v5.2c0 4.4-3 7.4-7 9.3-4-1.9-7-4.9-7-9.3V6z" />
    </IconBase>
  );
}

/** Disciplina: tarjeta. */
export function IconCard(props: IconProps) {
  return (
    <IconBase {...props}>
      <rect x="6" y="3.5" width="12" height="17" rx="2" />
    </IconBase>
  );
}

/** Buscar / jugadores parecidos: lupa. */
export function IconSearch(props: IconProps) {
  return (
    <IconBase {...props}>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <line x1="15.3" y1="15.3" x2="20.5" y2="20.5" />
    </IconBase>
  );
}

/** Valor de mercado: moneda. */
export function IconValue(props: IconProps) {
  return (
    <IconBase {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M14.5 9.3c-.5-.7-1.4-1.1-2.5-1.1-1.7 0-3 1.2-3 3s1.3 3 3 3c1.1 0 2-.4 2.5-1.1" />
      <line x1="8.5" y1="10.5" x2="13" y2="10.5" />
      <line x1="8.5" y1="13.2" x2="13" y2="13.2" />
    </IconBase>
  );
}

/** Ranking de goleadores: trofeo. */
export function IconTrophy(props: IconProps) {
  return (
    <IconBase {...props}>
      <path d="M8 4h8v5a4 4 0 0 1-8 0Z" />
      <path d="M8 5H5.5a2 2 0 0 0 0 4H8M16 5h2.5a2 2 0 0 1 0 4H16" />
      <path d="M12 13v3M9 20h6M10 17h4v3h-4Z" />
    </IconBase>
  );
}

/** Ranking de asistentes: diana de precisión. */
export function IconTarget(props: IconProps) {
  return (
    <IconBase {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4.5" />
      <circle cx="12" cy="12" r="0.75" fill={props.color ?? BRAND_COLOR} />
    </IconBase>
  );
}
