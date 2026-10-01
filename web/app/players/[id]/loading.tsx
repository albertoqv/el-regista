export default function Loading() {
  return (
    <div className="flex flex-col gap-8" aria-busy="true" aria-label="Cargando">
      <div className="grid grid-cols-1 gap-8 md:grid-cols-[320px_1fr]">
        <div className="skeleton aspect-[3/4] w-full rounded-lg" />
        <div className="flex flex-col justify-end gap-4">
          <div className="skeleton h-14 w-3/4 rounded-lg" />
          <div className="skeleton h-12 w-1/2 rounded-lg" />
          <div className="skeleton h-24 w-full rounded-lg" />
        </div>
      </div>
      <div className="skeleton h-96 w-full rounded-lg" />
    </div>
  );
}
