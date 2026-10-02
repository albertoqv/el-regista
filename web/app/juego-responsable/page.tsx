import type { Metadata } from "next";
import { External, LegalPage, LegalSection } from "@/app/components/LegalPage";

export const metadata: Metadata = {
  title: "Juego responsable · El Regista",
  description: "Los pronósticos de El Regista son probabilidades, no consejos de apuesta. Dónde pedir ayuda.",
};

export default function JuegoResponsablePage() {
  return (
    <LegalPage title="Juego responsable" updated="3 de octubre de 2026">
      <LegalSection title="Qué son nuestros pronósticos">
        <p>
          Probabilidades. Un 60% significa que, de cada diez partidos así, unos cuatro salen al revés.
          El historial lo muestra con todos sus fallos. Ningún modelo gana a las casas de apuestas de
          forma sostenida, tampoco este: con cuotas de cierre, el mercado acierta algo más.
        </p>
        <p>El Regista no es una casa de apuestas, no recomienda apostar y no cobra de nadie que lo haga.</p>
      </LegalSection>

      <LegalSection title="Si apuestas">
        <ul className="flex list-disc flex-col gap-1 pl-5">
          <li>Solo mayores de 18 años.</li>
          <li>Pon un límite de dinero y de tiempo antes de empezar, y no lo muevas.</li>
          <li>Nunca intentes recuperar lo perdido apostando más.</li>
          <li>Apostar no es una forma de ganar dinero.</li>
        </ul>
      </LegalSection>

      <LegalSection title="Dónde pedir ayuda">
        <p>
          Si el juego te preocupa a ti o a alguien cercano, la Dirección General de Ordenación del
          Juego reúne recursos y contactos de ayuda en{" "}
          <External href="https://www.ordenacionjuego.es/participantes-juego/juego-seguro">juego seguro</External>.
          También puedes inscribirte en el{" "}
          <External href="https://www.ordenacionjuego.es/participantes-juego/juego-seguro/rgiaj">registro de autoprohibición</External>{" "}
          para no poder jugar en ninguna web legal en España.
        </p>
      </LegalSection>
    </LegalPage>
  );
}
