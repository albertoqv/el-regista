import type { Metadata } from "next";
import { Reveal } from "@/app/components/Reveal";
import { Marker, ScoutNote } from "@/app/components/ScoutNote";

export const metadata: Metadata = {
  title: "Cómo funciona · El Regista",
  description: "De dónde salen los datos y cómo se calculan comparativas, gemelos y percentiles.",
};

function Section({ id, title, note, children }: { id: string; title: string; note?: string; children: React.ReactNode }) {
  return (
    <Reveal>
      <section id={id} className="glass scroll-mt-24 rounded-lg p-6 sm:p-8">
        {note && <ScoutNote rotate={-2} className="text-lg">{note}</ScoutNote>}
        <h2 className="font-heading text-2xl tracking-tight">{title}</h2>
        <div className="mt-3 flex flex-col gap-3 text-[15px] leading-relaxed text-ink/85 [&_strong]:text-ink">{children}</div>
      </section>
    </Reveal>
  );
}

export default function HowItWorksPage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <Reveal>
        <ScoutNote rotate={-3}>sin trucos ni cajas negras</ScoutNote>
        <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">
          Cómo <Marker color="#c93c17">funciona</Marker>
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
          estadísticas de 28 ligas más: primeras divisiones como Portugal, Países Bajos, Turquía o
          México, y las segundas de Inglaterra, España, Italia, Alemania, Francia, Países Bajos y
          Portugal.
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

    </div>
  );
}
