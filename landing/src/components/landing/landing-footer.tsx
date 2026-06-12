import Link from "next/link";
import { PackageOpen } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { GITHUB_URL, SITE_NAME } from "@/lib/site";

export function LandingFooter() {
  return (
    <footer className="border-t bg-card">
      <div className="mx-auto w-full max-w-7xl px-4 py-8 lg:px-8">
        <div className="flex flex-col gap-8 sm:flex-row sm:gap-12">
          <div className="sm:mr-auto">
            <Link href="/" className="inline-flex items-center gap-2">
              <PackageOpen className="size-5" />
              <span className="text-sm font-semibold tracking-tight">
                {SITE_NAME}
              </span>
            </Link>
            <p className="mt-3 max-w-xs text-sm text-muted-foreground">
              Isolierte Docker-Container für jeden Nutzer, selbst gehostet und
              Open Source.
            </p>
          </div>

          <div>
            <h5 className="mb-3 text-sm font-semibold">Projekt</h5>
            <ul className="space-y-2">
              <li>
                <a
                  href={GITHUB_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 flex flex-row items-center justify-between gap-4 border-t border-border/40 pt-8">
          <span className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} {SITE_NAME} · MIT-Lizenz
          </span>
          <ThemeToggle />
        </div>
      </div>
    </footer>
  );
}
