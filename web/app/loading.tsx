export default function Loading() {
  return (
    <div className="flex flex-col gap-8" aria-busy="true" aria-label="Cargando">
      <div className="skeleton mx-auto mt-16 h-16 w-3/4 rounded-2xl" />
      <div className="skeleton mx-auto h-14 w-full max-w-2xl rounded-2xl" />
      <div className="grid grid-cols-3 gap-4">
        <div className="skeleton aspect-[3/4] rounded-3xl" />
        <div className="skeleton aspect-[3/4] rounded-3xl" />
        <div className="skeleton aspect-[3/4] rounded-3xl" />
      </div>
    </div>
  );
}
