import type { NextConfig } from "next";

// openspawner.de is the canonical origin. Every other domain pointed at this
// app redirects there permanently so search engines index a single host.
const CANONICAL_ORIGIN = "https://openspawner.de";

const REDIRECT_HOSTS = [
  "www.openspawner.de",
  "openspawner.com",
  "www.openspawner.com",
  "openspawner.org",
  "www.openspawner.org",
  "openspawner.net",
  "www.openspawner.net",
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
    return REDIRECT_HOSTS.map((host) => ({
      source: "/:path*",
      has: [{ type: "host" as const, value: host }],
      destination: `${CANONICAL_ORIGIN}/:path*`,
      permanent: true,
    }));
  },
};

export default nextConfig;
