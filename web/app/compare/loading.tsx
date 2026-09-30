export default function Loading() {
  return (
    <div className="flex flex-col gap-8" aria-busy="true" aria-label="Cargando">
      <div className="skeleton h-12 w-2/3 rounded-2xl" />
      <div className="skeleton h-14 w-full rounded-2xl" />
      <div className="grid grid-cols-2 gap-8">
        <div className="skeleton aspect-[3/4] rounded-3xl" />
        <div className="skeleton aspect-[3/4] rounded-3xl" />
      </div>
    </div>
  );
}
