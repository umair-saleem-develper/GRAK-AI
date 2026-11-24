/** @type {import('next').NextConfig} */
const rawBackendUrl =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_URL ||
  "http://localhost:8001";
const backendUrl = rawBackendUrl.replace(/\/+$/, "");

const nextConfig = {
  compress: false, // Prevent Next.js from buffering SSE streams with GZIP
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: `${backendUrl}/api/auth/:path*`,
      },
      {
        source: "/user/:path*",
        destination: `${backendUrl}/api/auth/me`,
      },
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
