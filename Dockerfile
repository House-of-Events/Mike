FROM node:20.17.0-alpine3.20 as base

# Install PostgreSQL client
RUN apk add --no-cache postgresql-client

# Create app directory
RUN mkdir /app

WORKDIR /app

# Copy all project files into the container
COPY . .

# Copy package.json and install dependencies
COPY package.json package.json
RUN yarn install

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
CMD ["/app/entrypoint.sh"]