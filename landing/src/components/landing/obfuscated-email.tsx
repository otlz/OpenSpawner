"use client";

import { useSyncExternalStore } from "react";

type ObfuscatedEmailProps = {
  /** Local part before the @, e.g. "info" */
  user: string;
  /** Domain after the @, e.g. "example.org" */
  domain: string;
  className?: string;
};

// Hydration-safe "are we on the client yet?" flag. getServerSnapshot returns
// false so SSR (and the first, hydration-matching client render) show the
// fallback; after hydration the snapshot flips to true and the real address
// is rendered, all without a setState-in-effect.
const noop = () => () => {};
function useIsClient(): boolean {
  return useSyncExternalStore(
    noop,
    () => true,
    () => false,
  );
}

/**
 * E-mail address rendered as a clickable `mailto:` link that is assembled in
 * the browser, so the raw HTML never contains a scrapable "user@domain" string.
 *
 * Before hydration, and when JavaScript is disabled, the server-rendered
 * markup shows a human-readable "user [at] domain" fallback instead. That
 * keeps the address permanently available (per § 5 DDG) without handing a
 * ready-made address to harvesting bots, which only parse static HTML and
 * ignore scripts.
 */
export function ObfuscatedEmail({
  user,
  domain,
  className,
}: ObfuscatedEmailProps) {
  const isClient = useIsClient();

  // Pre-hydration / no-JavaScript fallback: not a valid e-mail pattern, so
  // standard harvesters skip it, but a human reads it instantly.
  if (!isClient) {
    return (
      <span>
        {user} [at] {domain.replace(/\./g, " [dot] ")}
      </span>
    );
  }

  const address = `${user}@${domain}`;
  return (
    <a
      href={`mailto:${address}`}
      className={
        className ??
        "underline underline-offset-2 transition-colors hover:text-foreground"
      }
    >
      {address}
    </a>
  );
}
