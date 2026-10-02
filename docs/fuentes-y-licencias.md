# Fuentes de datos y licencias

Nota interna (revisada el 2026-10-03). Hoy El Regista es gratuito y sin publicidad.
**Antes de cobrar, poner anuncios o vender datos, hay que revisar cada fuente con
calma (idealmente con alguien de derecho).** Esto no es asesoramiento legal.

| Fuente | Qué usamos | Licencia o condiciones (comprobado) | Riesgo si se monetiza |
|---|---|---|---|
| FBref vía Kaggle (`hubertsidorowicz/football-players-stats-*`) | Estadísticas por jugador y temporada | El dataset de Kaggle se publica como **MIT**, pero los datos son de FBref/Sports Reference (que a su vez los obtiene de Opta). Sports Reference tiene su propia política de uso de datos (`sports-reference.com/data_use.html`, 403 desde scripts: leerla en el navegador). | Alto: la licencia MIT del autor del dataset no puede ceder derechos que no tiene. |
| Transfermarkt, dataset de Kaggle (`davidcariboo/player-scores`) | Fotos (URL), altura, posición, valores, 9 ligas extra | Dataset **CC0**, pero el contenido sale de Transfermarkt. | Alto: revisar las condiciones de uso de Transfermarkt. |
| Transfermarkt web | Foto, fecha de nacimiento, pie, histórico de valor | robots.txt permite las fichas que usamos. Las fotos se enlazan, no se copian. | Alto, igual que arriba. Las fotos de jugadores tienen además derechos de imagen. |
| Understat | xG, xA, tiros, plantillas por partido, calendario | Su robots.txt dice `Disallow: /`. Uso aceptado con volumen mínimo. | Muy alto: lo primero que habría que sustituir. |
| football-data.co.uk | Córners, tarjetas, tiros, árbitro y cuotas | Descarga libre. Su aviso legal solo exime de responsabilidad; no encontramos una licencia explícita. Se financia con publicidad de casas de apuestas. | Medio: pedir permiso por escrito antes de un uso comercial. |
| Wikidata | Fechas de nacimiento | CC0. | Ninguno. |
| StatsBomb Open Data | 21 jugadores históricos | Licencia propia de StatsBomb (pide citarles). | Bajo para uso no comercial. |
| Fotos de ambiente (`web/lib/photos.ts`) | Cabeceras | CC BY / BY-SA / CC0, autores citados al pie. | Bajo si se mantiene la atribución. |

## Si algún día hay planes de pago

1. Sustituir Understat (por ejemplo, calcular nuestro propio xG con datos abiertos).
2. Pedir licencia a los proveedores, o mostrar solo métricas derivadas y agregadas.
3. Quitar las fotos de Transfermarkt o conseguir un proveedor con licencia.
4. Los pronósticos con cuotas pueden contar como publicidad de juego si hay
   afiliación con casas de apuestas (en España lo regula la DGOJ). Sin afiliación: solo
   aviso +18 y la página `/juego-responsable`.
