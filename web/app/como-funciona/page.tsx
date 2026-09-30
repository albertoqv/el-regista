import type { Metadata } from "next";
import Link from "next/link";
import { Reveal } from "@/app/components/motion";
import { Marker, ScoutNote } from "@/app/components/ScoutNote";
import { getBacktest, type Backtest } from "@/lib/api";
import { currentSeasonStartYear, seasonDisplay } from "@/lib/format";

export const metadata: Metadata = {
  title: "Cómo funciona · TalentScope",
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
          fill="#ffd76a"
          fillOpacity="0.85"
        >
          <title>{`Dice ${Math.round(bucket.predicted * 100)}% → pasó ${Math.round(bucket.observed * 100)}% (${bucket.count} casos)`}</title>
        </circle>
      ))}
      <text x={SIZE / 2} y={SIZE - 6} textAnchor="middle" className="fill-[#8b93a7] text-[10px]">
        probabilidad que da el modelo
      </text>
      <text x={10} y={SIZE / 2} textAnchor="middle" transform={`rotate(-90 10 ${SIZE / 2})`} className="fill-[#8b93a7] text-[10px]">
        frecuencia real
      </text>
    </svg>
  );
}

function Section({ id, title, note, children }: { id: string; title: string; note?: string; children: React.ReactNode }) {
  return (
    <Reveal>
      <section id={id} className="glass scroll-mt-24 rounded-3xl p-6 sm:p-8">
        {note && <ScoutNote rotate={-2} className="text-lg">{note}</ScoutNote>}
        <h2 className="font-display text-2xl font-bold tracking-tight">{title}</h2>
        <div className="mt-3 flex flex-col gap-3 text-[15px] leading-relaxed text-ink/85 [&_strong]:text-ink">{children}</div>
      </section>
    </Reveal>
  );
}

export default async function HowItWorksPage() {
  const season = String(currentSeasonStartYear() - 1);
  const backtest = await getBacktest(season).catch((): Backtest | null => null);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <Reveal>
        <ScoutNote rotate={-3}>sin trucos ni cajas negras</ScoutNote>
        <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">
          Cómo <Marker color="#ffd76a">funciona</Marker>
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
          <div className="mt-2 grid grid-cols-1 items-center gap-6 rounded-2xl bg-white/[0.03] p-4 sm:grid-cols-[1fr_300px]">
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
    </div>
  );
}
