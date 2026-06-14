import type { NextConfig } from "next";

// Each top-level domain serves the site directly and stays on its own host;
// the language is chosen per visitor (cookie -> Accept-Language), not per TLD.
// Only the "www." subdomain folds to the bare host of the SAME TLD so a single
// canonical host per domain is indexed (e.g. www.openspawner.com -> openspawner.com).
const BARE_HOSTS = [
  "openspawner.de",
  "openspawner.com",
  "openspawner.org",
  "openspawner.net",
];

const nextConfig: NextConfig = {
  output: "standalone",

  // The repo root contains a stray package-lock.json (shadcn CLI artifact),
  // which makes Next.js infer the wrong workspace root and nest the
  // standalone output. Pin the root so local and Docker builds match.
  turbopack: {
    root: __dirname,
  },

  async redirects() {
    return BARE_HOSTS.map((host) => ({
      source: "/:path*",
      has: [{ type: "host" as const, value: `www.${host}` }],
      destination: `https://${host}/:path*`,
      permanent: true,
    }));
  },
};

export default nextConfig;
