import { cookies, headers } from "next/headers";

import { DEFAULT_LOCALE, LOCALE_COOKIE, isLocale, type Locale } from "./config";

/**
 * Picks the language for the current request, server-side, so the very first
 * HTML the visitor (and any crawler) receives is already in the right language.
 *
 * Priority:
 *   1. The `locale` cookie  -> the visitor's explicit DE/EN choice always wins.
 *   2. The `Accept-Language` header -> "German browser -> German, otherwise English".
 *   3. DEFAULT_LOCALE (English) when nothing is detectable.
 *
 * Reading cookies/headers opts the route into dynamic rendering, which is fine
 * for this self-hosted Node (standalone) deployment.
 */
export async function resolveLocale(): Promise<Locale> {
  const cookieStore = await cookies();
  const fromCookie = cookieStore.get(LOCALE_COOKIE)?.value;
  if (isLocale(fromCookie)) {
    return fromCookie;
  }

  const headerStore = await headers();
  return detectFromAcceptLanguage(headerStore.get("accept-language"));
}

/**
 * Reads the highest-priority language from an `Accept-Language` header value.
 * Returns "de" only when German is the visitor's top preference; every other
 * language (and a missing/empty header) maps to the English default.
 *
 * Exported separately so the parsing is unit-testable without request context.
 */
export function detectFromAcceptLanguage(value: string | null): Locale {
  if (!value) {
    return DEFAULT_LOCALE;
  }

  const top = value
    .split(",")
    .map((part) => {
      const [tag, ...params] = part.trim().split(";");
      const qParam = params.find((p) => p.trim().startsWith("q="));
      const q = qParam ? Number.parseFloat(qParam.split("=")[1]) : 1;
      return { tag: tag.trim().toLowerCase(), q: Number.isNaN(q) ? 0 : q };
    })
    .filter((entry) => entry.tag.length > 0)
    .sort((a, b) => b.q - a.q)[0];

  return top?.tag.startsWith("de") ? "de" : DEFAULT_LOCALE;
}
