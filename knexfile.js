import dotenv from "dotenv";

dotenv.config();

const baseConfig = {
  client: 'postgresql',
  migrations: {
    directory: './db/migrations',
  },
  seeds: {
    directory: './db/seeds',
  },
  pool: {
    min: 2,
    max: 10,
  },
};

// Helper function to validate production config
const validateProductionConfig = () => {
  const requiredEnvVars = [
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_PORT",
  ];
  const missing = requiredEnvVars.filter((varName) => !process.env[varName]);

  if (missing.length > 0) {
    console.error("Missing required environment variables:", missing);
    throw new Error(
      `Missing required environment variables: ${missing.join(", ")}`,
    );
  }
};

const knexConfig = {
  development: {
    ...baseConfig,
    connection: {
      host: 'localhost',
      database: 'mike-docker',
      user: 'admin',
      password: 'admin',
      port: 5427,
    },
  },
  local: {
    ...baseConfig,
    connection: {
      host: 'db',
      database: 'mike-docker',
      user: 'admin',
      password: 'admin',
      port: 5432,
    },
  },
  production: {
    ...baseConfig,
    connection: () => {
      validateProductionConfig();
      return {
        host: process.env.DB_HOST,
        database: process.env.DB_NAME,
        user: process.env.DB_USER,
        password: String(process.env.DB_PASSWORD), // Ensure password is string
        port: parseInt(process.env.DB_PORT, 10),
        ssl: { rejectUnauthorized: false },
      };
    },
    pool: {
      min: 2,
      max: 10,
      // Add acquire and idle timeouts for Lambda environment
      acquireTimeoutMillis: 30000,
      createTimeoutMillis: 30000,
      idleTimeoutMillis: 30000,
      reapIntervalMillis: 1000,
      createRetryIntervalMillis: 200,
    },
  },
  docker: {
    ...baseConfig,
    connection: {
      host: "db",
      database: "mike-docker",
      user: "admin",
      password: "admin",
      port: 5432,
    },
  },
};

// Validate production config immediately if in production environment
if (process.env.NODE_ENV === "production") {
  validateProductionConfig();
}

export default knexConfig;
