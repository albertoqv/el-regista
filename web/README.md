# El Regista · web

Frontend en Next.js 16 de [El Regista](../README.md). Consume la API FastAPI del
repositorio raíz (`../src/`) y no tiene lógica de negocio propia.

```bash
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL
npm run dev
```

- Productos y navegación: `lib/products.ts`.
- Marca: tipografía en `app/fonts/`, logos en `public/brand/`, iconos en
  `app/components/icons.tsx` (se generan con `../scripts/brand/`).
- Fotos y sus créditos: `public/photos/` y `lib/photos.ts`.
