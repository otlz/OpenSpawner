/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    // INTERNAL_API_URL is for server-side rewrites (Docker networking)
    // Falls back to localhost:5000 for local development
    const apiUrl = process.env.INTERNAL_API_URL || 'http://localhost:5000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
