// Supported UI languages. German is the project's primary language; English is
// the international fallback. The site serves both from the same URLs and picks
// one per visitor (see detect.ts) rather than per domain or per path prefix.
export const LOCALES = ["de", "en"] as const;

export type Locale = (typeof LOCALES)[number];

// Ultimate fallback when neither a saved choice nor a detectable browser
// language is German. "German browser -> German, otherwise English."
export const DEFAULT_LOCALE: Locale = "en";

// Cookie that stores the visitor's explicit choice. Written by the DE/EN
// toggle and read on the server before detection, so the choice always wins.
export const LOCALE_COOKIE = "locale";

// One year, long enough to feel permanent without being indefinite.
export const LOCALE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

export function isLocale(value: string | null | undefined): value is Locale {
  return value === "de" || value === "en";
}
