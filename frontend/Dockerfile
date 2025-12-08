# Frontend Dockerfile (React)
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# For container-to-container API calls, set REACT_APP_API_BASE at runtime
ENV PORT=3000
EXPOSE 3000

CMD ["npm", "start"]

