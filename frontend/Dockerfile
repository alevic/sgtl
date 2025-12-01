# syntax=docker/dockerfile:1.6
FROM node:20-alpine

WORKDIR /app

# Instala dependencias usando cache e lockfile
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline

# Copia o restante da app
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
