# Dockerfile for webapp Next.js production
FROM node:20-alpine AS build
WORKDIR /app
# install dependencies
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
# copy source and build
COPY . .
RUN npm run build

# runtime image
FROM node:20-alpine AS runtime
WORKDIR /app
COPY --from=build /app .
ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080
# Serve the exported static files using a small static server
RUN npm install -g serve@latest
CMD ["serve", "out", "-s", "-l", "8080"]
