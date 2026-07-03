FROM node:20-alpine

WORKDIR /app

COPY package.json /app/package.json
COPY tsconfig.json /app/tsconfig.json
COPY next.config.mjs /app/next.config.mjs
COPY postcss.config.js /app/postcss.config.js
COPY tailwind.config.ts /app/tailwind.config.ts
COPY app /app/app
COPY components /app/components
COPY lib /app/lib

RUN npm install
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-p", "3000", "-H", "0.0.0.0"]
