import type { Metadata } from "next";
import { CONTACT_URL, External, LegalPage, LegalSection } from "@/app/components/LegalPage";

export const metadata: Metadata = {
  title: "Privacidad · El Regista",
  description: "Qué se mide en El Regista: visitas anónimas, sin cookies y sin guardar tu IP.",
};

export default function PrivacidadPage() {
  return (
    <LegalPage title="Privacidad" updated="3 de octubre de 2026">
      <LegalSection title="En corto">
        <p>
          No hay cuentas, ni formularios, ni cookies de seguimiento, ni publicidad. No sabemos quién
          eres y no queremos saberlo.
        </p>
      </LegalSection>

      <LegalSection title="Qué se cuenta">
        <p>Para saber cuánta gente usa la web se guarda, por cada página vista:</p>
        <ul className="flex list-disc flex-col gap-1 pl-5">
          <li>el día y la página (sin parámetros);</li>
          <li>la web de la que vienes, solo el dominio;</li>
          <li>
            un identificador que cambia cada día, calculado a partir de tu IP y tu navegador con una
            clave secreta. La IP no se guarda y el identificador no permite seguirte de un día a otro.
          </li>
        </ul>
        <p>
          Además, <External href="https://vercel.com/docs/analytics/privacy-policy">Vercel Web Analytics</External>{" "}
          mide visitas de forma agregada y sin cookies.
        </p>
      </LegalSection>

      <LegalSection title="Dónde están los datos">
        <p>
          La web se sirve desde Vercel y los datos se guardan en Railway. Ninguno de los dos recibe
          nada más que lo descrito arriba. Las fotos de jugadores se cargan desde Transfermarkt, que
          recibe la petición de tu navegador como con cualquier imagen enlazada.
        </p>
      </LegalSection>

      <LegalSection title="Cookies">
        <p>
          Ninguna para visitantes. Solo existe una cookie técnica en el panel privado del
          administrador, necesaria para iniciar sesión.
        </p>
      </LegalSection>

      <LegalSection title="Tus derechos">
        <p>
          Como no se guarda nada que te identifique, no hay datos personales que consultar o borrar.
          Si tienes cualquier duda, escribe en <External href={CONTACT_URL}>GitHub</External>. También
          puedes reclamar ante la{" "}
          <External href="https://www.aepd.es">Agencia Española de Protección de Datos</External>.
        </p>
      </LegalSection>
    </LegalPage>
  );
}
