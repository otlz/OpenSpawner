import type { MetadataRoute } from "next";

// Internal school platform: keep the whole host, including the user apps under
// /<slug>-<type>/, away from search engines and AI crawlers
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", disallow: "/" },
  };
}
