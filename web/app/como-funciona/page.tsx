import type { Metadata } from "next";
import Link from "next/link";
import { Reveal } from "@/app/components/motion";
import { Marker, ScoutNote } from "@/app/components/ScoutNote";
import {
  getBacktest,
  getPlayersBacktest,
  getStatsBacktest,
  type Backtest,
  type PlayersBacktest,
  type StatBacktest,
} from "@/lib/api";
import { currentSeasonStartYear, seasonDisplay } from "@/lib/format";

export const metadata: Metadata = {
  title: "Cómo funciona · El Regista",
  description: "De dónde salen los datos y cómo se calculan comparativas, gemelos y predicciones.",
};

const SIZE = 260;
const PAD = 30;

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/** Predicted probability (x) vs how often it happened (y): perfect = diagonal. */
function CalibrationChart({ backtest }: { backtest: Backtest }) {
  const scale = (value: number) => round(PAD + value * (SIZE - PAD * 2));
  const flip = (value: number) => round(SIZE - scale(value));
  const maxCount = Math.max(...backtest.calibration.map((b) => b.count), 1);
  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="h-auto w-full max-w-[320px]" role="img" aria-label="Calibración del modelo">
      <rect x={PAD} y={PAD} width={SIZE - PAD * 2} height={SIZE - PAD * 2} fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.1)" />
      <line x1={scale(0)} y1={flip(0)} x2={scale(1)} y2={flip(1)} stroke="rgba(255,255,255,0.35)" strokeDasharray="4 4" />
      {backtest.calibration.map((bucket) => (
        <circle
          key={bucket.predicted}
          cx={scale(bucket.predicted)}
          cy={flip(bucket.observed)}
          r={round(3 + 7 * Math.sqrt(bucket.count / maxCount))}
          fill="#9ccfea"
          fillOpacity="0.85"
        >
          <title>{`Dice ${Math.round(bucket.predicted * 100)}% → pasó ${Math.round(bucket.observed * 100)}% (${bucket.count} casos)`}</title>
        </circle>
      ))}
      <text x={SIZE / 2} y={SIZE - 6} textAnchor="middle" className="fill-[#c7b3b0] text-xs">
        probabilidad que da el modelo
      </text>
      <text x={10} y={SIZE / 2} textAnchor="middle" transform={`rotate(-90 10 ${SIZE / 2})`} className="fill-[#c7b3b0] text-xs">
        frecuencia real
      </text>
    </svg>
  );
}

function Section({ id, title, note, children }: { id: string; title: string; note?: string; children: React.ReactNode }) {
  return (
    <Reveal>
      <section id={id} className="glass scroll-mt-24 rounded-lg p-6 sm:p-8">
        {note && <ScoutNote rotate={-2} className="text-lg">{note}</ScoutNote>}
        <h2 className="font-display text-2xl font-bold tracking-tight">{title}</h2>
        <div className="mt-3 flex flex-col gap-3 text-[15px] leading-relaxed text-ink/85 [&_strong]:text-ink">{children}</div>
      </section>
    </Reveal>
  );
}

export default async function HowItWorksPage() {
  const season = String(currentSeasonStartYear() - 1);
  const [backtest, statsBacktest, playersBacktest] = await Promise.all([
    getBacktest(season).catch((): Backtest | null => null),
    getStatsBacktest("La Liga", season).catch((): StatBacktest[] => []),
    getPlayersBacktest("La Liga", season).catch((): PlayersBacktest | null => null),
  ]);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <Reveal>
        <ScoutNote rotate={-3}>sin trucos ni cajas negras</ScoutNote>
        <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">
          Cómo <Marker color="#9ccfea">funciona</Marker>
        </h1>
        <p className="mt-2 text-muted">
          Todo lo que ves sale de datos públicos y de cálculos que puedes entender. Aquí está cada uno
          explicado, con sus límites.
        </p>
        <nav className="mt-4 flex flex-wrap gap-2 text-xs">
          {[
            ["datos", "Datos"],
            ["percentiles", "Percentiles"],
            ["gemelos", "Gemelos"],
            ["cara-a-cara", "Cara a cara"],
            ["momentos", "Momentos"],
            ["equipos", "Equipos"],
            ["predicciones", "Predicciones"],
            ["estadisticas", "Córners y tarjetas"],
            ["jugadores", "Goleadores"],
          ].map(([id, label]) => (
            <a key={id} href={`#${id}`} className="rounded-full border border-line px-3 py-1 text-muted hover:text-ink">
              {label}
            </a>
          ))}
        </nav>
      </Reveal>

      <Section id="datos" title="De dónde salen los datos" note="todo gratis y público">
        <p>
          <strong>FBref</strong> (vía un dataset público de Kaggle que se regenera cada lunes): goles,
          asistencias, tiros, pases, regates, entradas, tarjetas y minutos de las 5 grandes ligas.
        </p>
        <p>
          <strong>Understat</strong>: goles esperados (xG), asistencias esperadas (xA), xGChain,
          xGBuildup, <strong>cada tiro de cada partido</strong> (minuto, posición en el campo, parte del
          cuerpo, situación y asistente), métricas por equipo (xG, presión PPDA, llegadas al área) y el
          calendario de próximos partidos.
        </p>
        <p>
          <strong>Transfermarkt</strong> (su web y un dataset público derivado): fotos, fecha de
          nacimiento, pie, altura, posición detallada, valor de mercado con su historial, y las
          estadísticas de 9 ligas más (Portugal, Países Bajos, Bélgica, Turquía, Escocia, Grecia,
          Dinamarca, Ucrania y Rusia).
        </p>
        <p>
          Se actualiza solo dos veces por semana (martes y viernes). Un mismo jugador se reconoce entre
          fuentes por nombre, año de nacimiento, equipo, minutos y goles; si dos candidatos encajan
          igual de bien, no se cruzan (preferimos un dato menos a un dato equivocado).
        </p>
      </Section>

      <Section id="percentiles" title="Percentiles y radar" note="compararse con los de su puesto">
        <p>
          Cada estadística se pasa a <strong>por 90 minutos</strong>, para que un titular y un suplente
          se puedan comparar. Después se calcula su <strong>percentil</strong> frente a los jugadores de
          su <strong>misma posición, liga y temporada</strong> que han jugado al menos el 30% de los
          minutos del más utilizado.
        </p>
        <p>
          Percentil 90 = mejor que el 90% de ellos. Los empates cuentan a medias. Si una fuente no mide
          algo esa temporada (por ejemplo, los pases en ligas sin datos avanzados), esa métrica no se
          muestra en lugar de salir a cero.
        </p>
      </Section>

      <Section id="gemelos" title="Gemelos: cómo sabemos que dos jugadores se parecen" note="lo más importante">
        <p>
          El &quot;estilo&quot; de un jugador es su perfil de percentiles: goles, xG, tiros, asistencias,
          xA, pases clave, participación en jugadas de peligro, regates, entradas, intercepciones… y
          también <strong>cómo marca</strong>: en el tramo final, de cabeza, desde fuera del área, a
          balón parado, su calidad de tiro y si define por encima de lo esperado.
        </p>
        <p>
          <strong>Similitud = 100 − la diferencia media de percentiles</strong> entre los dos, usando
          solo las métricas que ambos tienen (hacen falta al menos cinco). Un 90% significa que, de media,
          están a 10 puntos de percentil en cada faceta.
        </p>
        <p>
          Solo se proponen jugadores de la <strong>misma posición</strong> con una temporada reciente de
          al menos <strong>900 minutos</strong>, para que el perfil sea fiable. &quot;Se parecen en&quot;
          son las facetas donde el original destaca (percentil 60 o más) y el gemelo está más cerca;
          &quot;donde cambia&quot;, las diferencias de 20 puntos o más. El ahorro compara sus valores de
          mercado de Transfermarkt.
        </p>
      </Section>

      <Section id="cara-a-cara" title="Cara a cara y veredicto">
        <p>
          Métrica a métrica, gana quien tiene el valor mejor <strong>por 90 minutos</strong> (en faltas y
          tarjetas, gana quien tiene menos). El veredicto cuenta cuántas métricas gana cada uno y destaca
          las tres en las que la diferencia es mayor en proporción.
        </p>
      </Section>

      <Section id="momentos" title="Momentos de la temporada" note="sacado de cada tiro">
        <p>
          <strong>Tramo final</strong>: goles a partir del minuto 75. <strong>Goles decisivos</strong>:
          se reconstruye el marcador de cada partido tiro a tiro y cuenta un gol si empata el partido o
          pone a su equipo por delante (el 4-0 no cuenta). Un autogol suma para el rival.
        </p>
        <p>
          <strong>Desde fuera del área</strong>: con la posición del tiro en un campo de 105×68 m.{" "}
          <strong>Definición</strong>: goles sin penaltis menos xG sin penaltis (positivo = marca más de
          lo que marcaría un jugador medio con esas ocasiones). <strong>Calidad de tiro</strong>: xG medio
          por disparo, con un mínimo de 10 tiros.
        </p>
      </Section>

      <Section id="equipos" title="Equipos">
        <p>
          <strong>xPts</strong> (puntos esperados): los puntos que un equipo &quot;merece&quot; según las
          ocasiones de cada partido. Si alguien suma muchos más puntos que xPts, suele ser una racha de
          acierto que tiende a corregirse.
        </p>
        <p>
          <strong>PPDA</strong>: pases que el rival completa en su campo por cada acción defensiva
          (entrada, intercepción, falta). Cuanto más bajo, más presión. <strong>Llegadas</strong>: pases
          completados cerca del área rival.
        </p>
      </Section>

      <Section id="predicciones" title="Predicciones: el modelo" note="lo explicamos entero">
        <ol className="ml-5 list-decimal space-y-2">
          <li>
            Para cada equipo se estima una <strong>fuerza de ataque</strong> y una de{" "}
            <strong>defensa</strong> (1,0 = media de la liga) a partir de sus partidos de esta temporada y
            la anterior. El rendimiento de cada partido mezcla <strong>85% xG y 15% goles</strong>: el xG
            refleja mejor el nivel real, los goles corrigen a los que definen de forma sistemáticamente
            buena o mala.
          </li>
          <li>
            Los partidos recientes pesan más: el peso se reduce a la mitad cada <strong>120 días</strong>.
          </li>
          <li>
            Se <strong>ajusta por rival</strong> (marcar al mejor defensor vale más) resolviendo el
            sistema varias veces hasta que se estabiliza, y se <strong>ajusta por campo</strong> con la
            media real de goles en casa y fuera de cada liga.
          </li>
          <li>
            Con pocos partidos, las fuerzas se acercan a la media (como si cada equipo tuviera dos
            partidos &quot;normales&quot; de más), para que dos resultados raros no disparen el pronóstico.
          </li>
          <li>
            Goles esperados del partido = media de la liga en ese campo × ataque × defensa del rival. Con
            eso, una <strong>distribución de Poisson</strong> da la probabilidad de cada marcador, con la{" "}
            <strong>corrección de Dixon-Coles</strong> (en el fútbol real hay algo más de 0-0 y 1-1 de lo
            que predice Poisson). Sumando marcadores salen 1X2, más/menos de 2,5 y &quot;marcan ambos&quot;.
          </li>
        </ol>
        <p>
          Los parámetros (85/15, 120 días, etc.) no son a ojo: se eligieron probando combinaciones en la
          temporada 24/25 y se <strong>validaron en la 25/26</strong>, que no se usó para elegirlos.
        </p>

        {backtest && backtest.matches > 0 && (
          <div className="mt-2 grid grid-cols-1 items-center gap-6 rounded-lg bg-white/[0.03] p-4 sm:grid-cols-[1fr_300px]">
            <div className="flex flex-col gap-2 text-sm">
              <p>
                <strong>Examen real</strong>: los {backtest.matches.toLocaleString("es-ES")} partidos de
                la {seasonDisplay(season)}, cada uno pronosticado solo con datos anteriores a él.
              </p>
              <p>
                Acierta el resultado el <strong>{Math.round(backtest.accuracy * 100)}%</strong> de las
                veces (apostar siempre por lo más habitual acierta el{" "}
                {Math.round(backtest.baseline_accuracy * 100)}%).
              </p>
              <p>
                Puntuación Brier <strong>{backtest.brier.toFixed(3)}</strong> frente a{" "}
                {backtest.baseline_brier.toFixed(3)} de la referencia (menos es mejor; lanzar una moneda de
                tres caras daría 0,667). Como orientación, las casas de apuestas suelen rondar 0,57-0,58.
              </p>
              <p>
                El gráfico muestra la <strong>calibración</strong>: cuando el modelo dice 30%, ¿pasa un
                30%? Cuanto más cerca de la diagonal, más honestas son sus probabilidades.
              </p>
            </div>
            <CalibrationChart backtest={backtest} />
          </div>
        )}

        <p className="text-sm text-muted">
          Límites: no sabe de lesiones, sanciones, rotaciones, cambios de entrenador ni del mercado de
          fichajes hasta que se reflejan en los partidos. A principio de temporada tira más de la anterior.
          Úsalo como una opinión informada, no como una certeza.{" "}
          <Link href="/predicciones" className="text-brand-2 hover:underline">
            Ver predicciones →
          </Link>
        </p>
      </Section>

      <Section id="estadisticas" title="Córners, tarjetas, faltas y tiros" note="con sus límites a la vista">
        <p>
          Los datos de cada partido salen de <strong>football-data.co.uk</strong>: córners, tarjetas,
          faltas, tiros y tiros a puerta de cada equipo, y las cuotas de las casas de apuestas. Para cada
          estadística, cada equipo tiene una tendencia <strong>a favor</strong> (cuántos saca) y{" "}
          <strong>en contra</strong> (cuántos concede), calculadas igual que la fuerza en goles: más peso a
          lo reciente, ajuste por rival y por campo, y prudencia con pocos partidos.
        </p>
        <p>
          Como estas cifras varían más de lo que predice una distribución de Poisson, cada equipo se
          modela con una <strong>binomial negativa</strong> cuya dispersión se mide en cada liga. De ahí
          salen el total esperado, quién saca más y cada línea de más/menos. En tarjetas, si se conoce el{" "}
          <strong>árbitro</strong> (hoy solo en la Premier), se ajusta por su media de amarillas.
        </p>
        <p>
          En el <strong>ganador del partido</strong> mostramos también la probabilidad de las casas de
          apuestas (sus cuotas sin el margen). Lo hemos medido: en la temporada 25/26 las cuotas de
          cierre aciertan más que nuestro modelo y que cualquier mezcla de ambos, porque saben de
          lesiones y alineaciones. Por eso, cuando hay cuotas, son la referencia principal del 1X2, y
          nuestro modelo queda como opinión independiente.
        </p>
        {statsBacktest.length > 0 && (
          <div className="overflow-x-auto rounded-lg bg-white/[0.03] p-4">
            <p className="mb-2 text-sm">
              <strong>Examen real</strong> en La Liga {seasonDisplay(season)}: error medio del total del
              partido, frente a usar siempre la media de la liga (menos es mejor).
            </p>
            <table className="w-full min-w-[420px] text-sm">
              <thead>
                <tr className="text-left text-xs text-muted">
                  <th className="py-1">Estadística</th>
                  <th className="text-right">Modelo</th>
                  <th className="text-right">Media de la liga</th>
                  <th className="text-right">Veredicto</th>
                </tr>
              </thead>
              <tbody>
                {statsBacktest.map((row) => {
                  const gain = (row.baseline_mae - row.model_mae) / row.baseline_mae;
                  return (
                    <tr key={row.stat} className="border-t border-line/60">
                      <td className="py-1.5">{STAT_NAMES[row.stat] ?? row.stat}</td>
                      <td className="text-right tabular-nums">{row.model_mae.toFixed(2)}</td>
                      <td className="text-right tabular-nums text-muted">{row.baseline_mae.toFixed(2)}</td>
                      <td
                        className={`text-right text-xs ${gain > 0.02 ? "text-brand-2" : gain > 0 ? "text-ink/80" : "text-rose-300"}`}
                      >
                        {gain > 0.02 ? "mejor" : gain > 0 ? "algo mejor" : "igual o peor"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-muted">
              Las tarjetas dependen mucho del árbitro y del contexto (derbis, lo que se juega cada uno), y
              ahí el modelo apenas mejora a la media: tómalas con más cautela que el resto.
            </p>
          </div>
        )}
      </Section>

      <Section id="jugadores" title="Goleadores, asistentes y amonestados" note="jugador a jugador">
        <p>
          Con la alineación de cada partido (minutos, tiros, xG, xA y tarjetas de cada jugador, de
          Understat) se calcula para cada futbolista:
        </p>
        <ol className="ml-5 list-decimal space-y-1">
          <li>
            <strong>Minutos esperados</strong>: la media de sus minutos en los últimos 6 partidos de su
            equipo, dando más peso a los más recientes (si no jugó, cuenta 0). Si lleva semanas sin jugar,
            baja solo.
          </li>
          <li>
            <strong>Ritmos por 90 minutos</strong> de xG, xA, tiros y amarillas, acercados a la media de su
            posición cuando ha jugado poco: un gol afortunado no convierte a un central en goleador.
          </li>
          <li>
            <strong>El partido</strong>: si el modelo espera que su equipo marque más de lo habitual ante
            ese rival, todos sus atacantes suben en proporción.
          </li>
        </ol>
        <p>
          Probabilidad de marcar = 1 − e<sup>−λ</sup>, con λ = ritmo × minutos/90 × ajuste del partido
          (igual para asistencia, tarjeta y tiros).
        </p>
        {playersBacktest && playersBacktest.predictions > 0 && (
          <p className="rounded-lg bg-white/[0.03] p-4 text-sm">
            <strong>Examen real</strong> en La Liga {seasonDisplay(season)}:{" "}
            {playersBacktest.predictions.toLocaleString("es-ES")} pronósticos de &quot;marca&quot; hechos
            solo con datos anteriores. Brier <strong>{playersBacktest.brier.toFixed(3)}</strong> frente a{" "}
            {playersBacktest.baseline_brier.toFixed(3)} de dar a todos la misma probabilidad.
          </p>
        )}
        <p className="text-sm text-muted">
          Límite: sin alineaciones confirmadas, un titular que descansa ese día sigue apareciendo con sus
          minutos habituales.
        </p>
      </Section>
    </div>
  );
}

const STAT_NAMES: Record<string, string> = {
  corners: "Córners",
  yellows: "Amarillas",
  fouls: "Faltas",
  shots: "Tiros",
  shots_on_target: "Tiros a puerta",
};
