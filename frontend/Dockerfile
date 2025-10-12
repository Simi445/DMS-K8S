FROM node:22.20.0-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install --peer-legacy-deps

COPY . .


FROM node:22.20.0-alpine

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]