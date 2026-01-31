# Build stage
FROM node:20.11-alpine AS builder

WORKDIR /app

# Copy nur package.json (Layer Caching - schneller Rebuilds wenn Source-Code aendert)
COPY package*.json ./

# Installiere alle Packages (incl. devDependencies fuer TypeScript Build)
RUN npm ci --prefer-offline --no-audit && \
    npm cache clean --force

# Copy Source Code
COPY . .

# Build Next.js App (generiert /app/.next output)
RUN npm run build

# Production stage - serve static files with nginx
FROM nginx:alpine

# Copy nur das Build-Output (Rest wird nicht mehr benoetigt)
COPY --from=builder /app/out /usr/share/nginx/html

# Nginx config fuer SPA (Single Page App)
RUN echo 'server { \
    listen 8080; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
