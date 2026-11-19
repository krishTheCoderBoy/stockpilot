# Dev image: runs the Vite dev server with hot reload. A production build (static assets
# behind a web server) is a Phase 5 concern.
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
