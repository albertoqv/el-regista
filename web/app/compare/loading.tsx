export default function Loading() {
  return (
    <div className="flex flex-col gap-8" aria-busy="true" aria-label="Cargando">
      <div className="skeleton h-12 w-2/3 rounded-lg" />
      <div className="skeleton h-14 w-full rounded-lg" />
      <div className="grid grid-cols-2 gap-8">
        <div className="skeleton aspect-[3/4] rounded-lg" />
        <div className="skeleton aspect-[3/4] rounded-lg" />
      </div>
    </div>
  );
}
