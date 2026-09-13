/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker deployment.
  // This bundles only the minimal server and dependencies needed to run.
  output: "standalone",

  // Disable the X-Powered-By header for security
  poweredByHeader: false,
};

export default nextConfig;
