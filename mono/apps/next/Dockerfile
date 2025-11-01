# Multi-stage build for Next.js frontend
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package.json yarn.lock* .yarnrc.yml ./
COPY .yarn ./.yarn
COPY packages/prisma/package.json ./packages/prisma/
COPY packages/universal/package.json ./packages/universal/
COPY apps/next/package.json ./apps/next/

# Install dependencies
RUN corepack enable && \
    yarn install --immutable

# Build universal packages
FROM base AS universal-builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY packages/universal ./packages/universal
COPY tsconfig.base.json ./
RUN cd packages/universal && yarn build

# Build Next.js app
FROM base AS builder
WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY --from=universal-builder /app/packages/universal ./packages/universal

# Copy app source
COPY apps/next ./apps/next
COPY tsconfig.base.json turbo.json ./

# Build Next.js
RUN cd apps/next && yarn build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built app
COPY --from=builder --chown=nextjs:nodejs /app/apps/next/.next ./apps/next/.next
COPY --from=builder --chown=nextjs:nodejs /app/apps/next/public ./apps/next/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/next/package.json ./apps/next/
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/packages ./packages

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Run Next.js
CMD ["node", "apps/next/.next/standalone/apps/next/server.js"]

