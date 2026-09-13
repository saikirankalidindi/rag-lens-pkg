# ─────────────────────────────────────────────────────────────
#  RAGLens Web — Dockerfile
#  Multi-stage build: deps → build → slim runtime.
#  Build context: repo root (so we can COPY apps/web/)
# ─────────────────────────────────────────────────────────────

# ── Stage 1: install dependencies ─────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app

# Install libc compat for node native modules on Alpine
RUN apk add --no-cache libc6-compat

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci --prefer-offline


# ── Stage 2: build ────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY apps/web/ ./

# NEXT_PUBLIC_ vars must be available at build time
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build


# ── Stage 3: production runtime ───────────────────────────────
FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy the standalone build output (requires `output: 'standalone'` in next.config)
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
