# =============================================================================
# Stage 1: Build React/Vite Application
# =============================================================================
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package manifests
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code and build config
COPY . .

# Build production assets (outputs to /app/dist)
RUN npm run build

# =============================================================================
# Stage 2: Production Nginx Server
# =============================================================================
FROM nginx:alpine AS runner

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built application assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with API proxy and SPA fallback
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
