module.exports = {
  development: {
    client: "pg", // Use pg client for PostgreSQL
    connection: {
      host: "db", // The service name for the PostgreSQL container in Docker Compose
      user: "admin",
      password: "admin",
      database: "mike-docker",
    },
    migrations: {
      directory: "./db/migrations", // Path to migrations
    },
    seeds: {
      directory: "./db/seeds", // Path to seeds
    },
  },
};
