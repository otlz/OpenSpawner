import Image from "next/image";

import { FadeInView } from "@/components/animation/fade-in-view";

export function PreviewSection() {
  return (
    <section className="pb-16 md:pb-24">
      <div className="mx-auto w-full max-w-6xl px-4 lg:px-8">
        <FadeInView>
          <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
            {/* Minimal browser frame around the dashboard screenshot. */}
            <div className="flex items-center gap-1.5 border-b px-4 py-3">
              <span className="size-2.5 rounded-full bg-muted-foreground/25" />
              <span className="size-2.5 rounded-full bg-muted-foreground/25" />
              <span className="size-2.5 rounded-full bg-muted-foreground/25" />
              <span className="ml-3 truncate text-xs text-muted-foreground">
                coder.openspawner.de/dashboard
              </span>
            </div>
            <Image
              src="/dashboard.png"
              alt="Das OpenSpawner-Dashboard mit dem Vorlagen-Katalog, gruppiert nach Anwendungen, Betriebssystemen und Datenbanken."
              width={1920}
              height={1080}
              priority
              sizes="(max-width: 1152px) 100vw, 1152px"
              className="h-auto w-full"
            />
          </div>
        </FadeInView>
      </div>
    </section>
  );
}
