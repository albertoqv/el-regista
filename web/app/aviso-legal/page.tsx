import type { Metadata } from "next";
import Link from "next/link";
import { CONTACT_URL, External, LegalPage, LegalSection } from "@/app/components/LegalPage";

export const metadata: Metadata = {
  title: "Aviso legal · El Regista",
  description: "Quién está detrás de El Regista, de dónde salen los datos y qué uso se puede hacer de ellos.",
};

export default function AvisoLegalPage() {
  return (
    <LegalPage title="Aviso legal" updated="3 de octubre de 2026">
      <LegalSection title="Quién lo hace">
        <p>
          El Regista es un proyecto personal, gratuito y sin publicidad. No vende nada ni cobra por
          ningún servicio. Para cualquier consulta, corrección o petición de retirada de contenido,
          escribe en <External href={CONTACT_URL}>GitHub</External>.
        </p>
      </LegalSection>

      <LegalSection title="Los datos">
        <p>
          Las estadísticas proceden de fuentes públicas: FBref (a través de Kaggle), Understat,
          Transfermarkt y football-data.co.uk. Pertenecen a sus autores; aquí se muestran
          procesadas, con fines informativos y citando su origen. Pueden contener errores o llegar
          con retraso.
        </p>
        <p>
          Las fotos de jugadores son de Transfermarkt. Las fotos de ambiente tienen licencia libre y
          sus autores aparecen al pie de cada página.
        </p>
      </LegalSection>

      <LegalSection title="Los pronósticos">
        <p>
          Son probabilidades calculadas por un modelo estadístico, no consejos de apuesta ni
          garantías de resultado. El Regista no es un operador de juego ni tiene acuerdos con casas de
          apuestas. Más en <Link href="/juego-responsable" className="font-semibold underline decoration-line underline-offset-4 hover:text-brand">juego responsable</Link>.
        </p>
      </LegalSection>

      <LegalSection title="Responsabilidad">
        <p>
          Se intenta que todo sea correcto, pero no se garantiza. El uso de la información es
          responsabilidad de quien la usa. Los enlaces a otras webs no implican relación con ellas.
        </p>
      </LegalSection>

      <LegalSection title="Marca y código">
        <p>
          El nombre, el logo y la tipografía Regista Display son propios del proyecto. Los nombres de
          clubes, competiciones y jugadores pertenecen a sus titulares y se usan solo para
          identificarlos.
        </p>
      </LegalSection>
    </LegalPage>
  );
}
