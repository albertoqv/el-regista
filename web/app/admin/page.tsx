import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";
import { login, logout } from "@/app/admin/actions";
import { ADMIN_COOKIE, getAdminDashboard, type AdminDashboard, type RankedCount } from "@/lib/admin";

export const metadata: Metadata = {
  title: "Panel · El Regista",
  robots: { index: false, follow: false },
};

const DATA_LABELS: Record<string, string> = {
  players: "Jugadores",
  players_with_photo: "Con foto",
  player_seasons: "Temporadas de jugador",
  competitions: "Competiciones",
  matches_with_shots: "Partidos con tiros",
  shots: "Tiros",
  match_stats: "Partidos con estadísticas",
  fixtures: "Partidos (Understat)",
};

const PAGE_LABELS: Record<string, string> = {
  "/": "Portada",
  "/gemelos": "Gemelos",
  "/explorar": "Explorador",
  "/compare": "Comparador",
  "/equipos": "Equipos",
  "/predicciones": "Predicciones",
  "/como-funciona": "Cómo funciona",
};

function pageLabel(path: string): string {
  if (PAGE_LABELS[path]) return PAGE_LABELS[path];
  if (path.startsWith("/players/")) return `Ficha de jugador ${path.split("/")[2]}`;
  if (path.startsWith("/predicciones/")) return `Partido ${path.split("/")[2]}`;
  if (path.startsWith("/equipos/")) return `Equipo: ${decodeURIComponent(path.split("/")[2])}`;
  return path;
}

function dollars(value: number): string {
  return `${value.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} $`;
}

function number(value: number): string {
  return value.toLocaleString("es-ES");
}

function people(value: number): string {
  return `${number(value)} ${value === 1 ? "persona" : "personas"}`;
}

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "short", timeZone: "Europe/Madrid" });
}

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="glass rounded-lg p-5">
      <p className="text-xs font-semibold text-muted">{label}</p>
      <p className="mt-1 font-display text-3xl font-bold tabular-nums">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </div>
  );
}

function VisitsChart({ daily }: { daily: AdminDashboard["daily"] }) {
  const width = 720;
  const height = 170;
  const max = Math.max(1, ...daily.map((day) => day.views));
  const slot = width / daily.length;
  const bar = Math.max(2, Math.round(slot * 0.62));
  return (
    <svg viewBox={`0 0 ${width} ${height + 22}`} className="w-full" role="img">
      <title>Visitas por día</title>
      {daily.map((day, index) => {
        const x = Math.round(index * slot + (slot - bar) / 2);
        const viewsHeight = Math.round((day.views / max) * height);
        const peopleHeight = Math.round((day.visitors / max) * height);
        const label = `${shortDate(day.day)}: ${day.views} visitas, ${day.visitors} personas`;
        return (
          <g key={day.day}>
            <title>{label}</title>
            <rect x={x} y={height - viewsHeight} width={bar} height={viewsHeight} rx={3} fill="#9ccfea" opacity={0.35} />
            <rect x={x} y={height - peopleHeight} width={bar} height={peopleHeight} rx={3} fill="#9ccfea" />
            {index % 5 === 0 || index === daily.length - 1 ? (
              <text
                x={index === 0 ? x : index === daily.length - 1 ? x + bar : x + Math.round(bar / 2)}
                y={height + 16}
                textAnchor={index === 0 ? "start" : index === daily.length - 1 ? "end" : "middle"} fontSize={11} fill="currentColor" opacity={0.55}>
                {shortDate(day.day)}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

function Ranking({ title, rows, label }: { title: string; rows: RankedCount[]; label: (name: string) => string }) {
  const max = Math.max(1, ...rows.map((row) => row.views));
  return (
    <section className="glass rounded-lg p-5">
      <h2 className="font-display text-lg font-bold">{title}</h2>
      {rows.length === 0 ? (
        <p className="mt-3 text-sm text-muted">Todavía nada.</p>
      ) : (
        <ol className="mt-3 flex flex-col gap-1.5">
          {rows.map((row) => (
            <li key={row.name} className="relative overflow-hidden rounded-xl px-3 py-1.5 text-sm">
              <span className="absolute inset-y-0 left-0 rounded-xl bg-white/[0.06]" style={{ width: `${(row.views / max) * 100}%` }} />
              <span className="relative flex justify-between gap-3">
                <span className="truncate">{label(row.name)}</span>
                <span className="shrink-0 tabular-nums text-muted">
                  {number(row.views)} · {number(row.visitors)} pers.
                </span>
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function LoginForm({ error }: { error?: string }) {
  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 py-16">
      <h1 className="font-display text-4xl font-bold tracking-tight">Panel</h1>
      <p className="text-sm text-muted">
        Visitas, coste del servidor y salud de la API. Entra con la clave de ingesta (la misma de
        <code className="mx-1">INGESTION_API_KEY</code>). Se guarda en una cookie solo para esta
        página.
      </p>
      {error ? <p className="rounded-xl bg-red-500/15 px-3 py-2 text-sm text-red-300">{error}</p> : null}
      <form action={login} className="flex gap-2">
        <input
          name="key"
          type="password"
          required
          autoComplete="current-password"
          placeholder="Clave"
          className="glass flex-1 rounded-xl px-3 py-2 text-sm text-ink outline-none"
        />
        <button type="submit" className="rounded-full bg-[#9ccfea] px-5 py-2 text-sm font-bold text-bg">
          Entrar
        </button>
      </form>
    </div>
  );
}

export default async function AdminPage() {
  const key = (await cookies()).get(ADMIN_COOKIE)?.value;
  if (!key) return <LoginForm />;
  const dashboard = await getAdminDashboard(key);
  if (dashboard === "unauthorized") return <LoginForm error="Clave incorrecta." />;
  if (dashboard === "unavailable") {
    return <LoginForm error="La API no responde ahora mismo. Prueba en un minuto." />;
  }

  const hosting = dashboard.hosting;
  const lineItems = hosting ? Object.entries(hosting.line_items).sort((a, b) => b[1] - a[1]) : [];
  const lineMax = Math.max(0.0001, ...lineItems.map(([, value]) => value));
  const api = dashboard.api;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-4xl font-bold tracking-tight">Panel</h1>
          <p className="text-sm text-muted">
            Últimos {dashboard.days} días. Visitas contadas sin cookies ni IP (un visitante = una
            persona en un día; bots excluidos).
          </p>
        </div>
        <form action={logout}>
          <button type="submit" className="rounded-full border border-line px-4 py-2 text-sm text-muted hover:text-ink">
            Salir
          </button>
        </form>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Visitas hoy" value={number(dashboard.views_today)} hint={people(dashboard.visitors_today)} />
        <Kpi label={`Visitas ${dashboard.days} días`} value={number(dashboard.views_period)} hint={`${number(dashboard.visitors_period)} visitantes diarios sumados`} />
        <Kpi
          label="Coste servidor (periodo)"
          value={hosting ? dollars(hosting.current_dollars) : "—"}
          hint={hosting?.estimated_dollars != null ? `Estimado al cierre: ${dollars(hosting.estimated_dollars)}` : "Railway sin conectar"}
        />
        <Kpi label="Web (Vercel Hobby)" value="0,00 $" hint="Plan gratuito" />
      </div>

      <section className="glass rounded-lg p-5">
        <div className="flex items-baseline justify-between">
          <h2 className="font-display text-lg font-bold">Visitas por día</h2>
          <span className="text-xs text-muted">
            <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-[#9ccfea]" />personas
            <span className="ml-3 mr-1 inline-block h-2 w-2 rounded-sm bg-[#9ccfea]/35" />páginas vistas
          </span>
        </div>
        <VisitsChart daily={dashboard.daily} />
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <Ranking title="Páginas más vistas" rows={dashboard.top_pages} label={pageLabel} />
        <Ranking title="De dónde llegan" rows={dashboard.top_referrers} label={(name) => name} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="glass flex flex-col gap-3 rounded-lg p-5">
          <h2 className="font-display text-lg font-bold">Servidor (Railway)</h2>
          {hosting ? (
            <>
              <p className="text-sm text-muted">
                Periodo de facturación {shortDate(hosting.period_start)} – {shortDate(hosting.period_end)}.
                {hosting.usage_limit_dollars
                  ? ` Límite de gasto: ${dollars(hosting.usage_limit_dollars)}.`
                  : " Sin límite de gasto configurado."}
              </p>
              <ul className="flex flex-col gap-1.5">
                {lineItems.map(([label, value]) => (
                  <li key={label} className="relative overflow-hidden rounded-xl px-3 py-1.5 text-sm">
                    <span className="absolute inset-y-0 left-0 rounded-xl bg-[#f28c6b]/20" style={{ width: `${(value / lineMax) * 100}%` }} />
                    <span className="relative flex justify-between">
                      <span>{label}</span>
                      <span className="tabular-nums">{dollars(value)}</span>
                    </span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-muted">
                Precios de Railway: 10 $/GB de memoria al mes y 20 $/vCPU al mes. La memoria encendida
                24 h es casi todo el coste.
              </p>
            </>
          ) : dashboard.hosting_configured ? (
            <p className="text-sm text-red-300">Railway no respondió: {dashboard.hosting_error}</p>
          ) : (
            <p className="text-sm text-muted">
              Para ver aquí el coste, crea un token de workspace en Railway (Account Settings →
              Tokens) y añádelo al servicio <code>api</code> como <code>RAILWAY_API_TOKEN</code>, junto
              a <code>RAILWAY_WORKSPACE_ID</code>. Mientras, lo tienes con <code>railway usage</code>.
            </p>
          )}
          <a href="https://railway.com/dashboard" target="_blank" rel="noreferrer" className="text-sm text-brand-2 hover:underline">
            Abrir Railway →
          </a>
        </section>

        <section className="glass flex flex-col gap-3 rounded-lg p-5">
          <h2 className="font-display text-lg font-bold">Salud de la API</h2>
          <p className="text-sm text-muted">Desde el último despliegue ({shortDate(api.since)}).</p>
          <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <div><p className="text-xs text-muted">Peticiones</p><p className="font-display text-xl font-bold tabular-nums">{number(api.requests)}</p></div>
            <div><p className="text-xs text-muted">Errores 5xx</p><p className={`font-display text-xl font-bold tabular-nums ${api.server_errors ? "text-red-300" : ""}`}>{number(api.server_errors)}</p></div>
            <div><p className="text-xs text-muted">Mediana</p><p className="font-display text-xl font-bold tabular-nums">{Math.round(api.p50_ms)} ms</p></div>
            <div><p className="text-xs text-muted">p95</p><p className="font-display text-xl font-bold tabular-nums">{Math.round(api.p95_ms)} ms</p></div>
          </div>
          {api.slow_routes.length ? (
            <div className="text-sm">
              <p className="text-xs text-muted">Lentas (&gt;2 s)</p>
              <ul>{api.slow_routes.map(([route, count]) => <li key={route} className="flex justify-between"><code className="truncate">{route}</code><span className="tabular-nums">{count}</span></li>)}</ul>
            </div>
          ) : null}
          <div className="text-sm">
            <p className="text-xs text-muted">Más pedidas</p>
            <ul>{api.top_routes.slice(0, 6).map(([route, count]) => <li key={route} className="flex justify-between gap-3"><code className="truncate">{route}</code><span className="tabular-nums text-muted">{number(count)}</span></li>)}</ul>
          </div>
        </section>
      </div>

      <section className="glass rounded-lg p-5">
        <h2 className="font-display text-lg font-bold">Datos</h2>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Object.entries(dashboard.data).map(([key, value]) => (
            <div key={key}>
              <p className="text-xs text-muted">{DATA_LABELS[key] ?? key}</p>
              <p className="font-display text-xl font-bold tabular-nums">{number(value)}</p>
            </div>
          ))}
        </div>
      </section>

      <p className="text-xs text-muted">
        También tienes las visitas de Vercel (Web Analytics, gratis en Hobby) en{" "}
        <a href="https://vercel.com/dashboard" target="_blank" rel="noreferrer" className="text-brand-2 hover:underline">
          vercel.com/dashboard
        </a>{" "}
        → proyecto <code>web</code> → Analytics. <Link href="/" className="text-brand-2 hover:underline">Volver a la web</Link>
      </p>
    </div>
  );
}
