import Image from "next/image";
import type { ReactNode } from "react";

/** Page title over a real football photo, darkened towards the text. */
export function PageHeader({
  photo,
  title,
  children,
}: {
  photo: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="photo-header -mx-4 -mt-6 flex min-h-[220px] flex-col justify-end gap-2 px-4 pb-6 pt-16 sm:mx-0 sm:mt-0 sm:min-h-[260px] sm:rounded-xl sm:px-8">
      <Image src={photo} alt="" fill sizes="(min-width: 1152px) 1104px, 100vw" className="object-cover" loading="eager" fetchPriority="high" />
      <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">{title}</h1>
      {children ? <div className="text-base text-ink/85">{children}</div> : null}
    </header>
  );
}
