"use client";

import { LOCALES } from "@/lib/i18n/config";
import { useLocale } from "@/components/i18n/locale-provider";
import { cn } from "@/lib/utils";

/**
 * Compact DE | EN segmented control for the navbar. Matches the height of the
 * outline GitHub button next to it (h-8). The active language is highlighted;
 * clicking the other one switches and remembers the choice.
 */
export function LanguageToggle() {
  const { locale, setLocale, dict } = useLocale();

  return (
    <div
      role="group"
      aria-label={dict.nav.switchLanguage}
      className="inline-flex h-8 items-center rounded-lg border border-border bg-background p-0.5 dark:border-input dark:bg-input/30"
    >
      {LOCALES.map((option) => {
        const isActive = option === locale;
        return (
          <button
            key={option}
            type="button"
            onClick={() => setLocale(option)}
            aria-pressed={isActive}
            className={cn(
              "inline-flex h-full items-center rounded-md px-2 text-xs font-medium uppercase transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
              isActive
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {option}
          </button>
        );
      })}
    </div>
  );
}
