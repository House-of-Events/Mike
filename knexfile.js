import dotenv from "dotenv";
import { execSync } from 'child_process';

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

// Helper function to get Chamber secrets
function getChamberSecrets(service) {
  const requiredKeys = [
    'db_host',
    'db_port',
    'db_name',
    'db_username',
    'db_password'
  ];
  
  const secrets = {};
  
  requiredKeys.forEach(key => {
    try {
      const value = execSync(`chamber read ${service} ${key} -q`).toString().trim();
      secrets[key] = value;
    } catch (error) {
      console.error(`Error reading ${key} from ${service}:`, error.message);
      process.exit(1);
    }
  });
  return secrets;
}

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
      // Try to get secrets from Chamber first, fallback to environment variables
      let dbConfig;
      
      try {
        console.log("Getting secrets from Chamber for production environment");
        const appSecrets = getChamberSecrets('app-aws');
        dbConfig = {
          host: appSecrets.db_host,
          database: appSecrets.db_name,
          user: appSecrets.db_username,
          password: appSecrets.db_password,
          port: parseInt(appSecrets.db_port, 10),
          ssl: { rejectUnauthorized: false },
        };
      } catch (error) {
        console.error("Chamber not available, falling back to environment variables", error);
        validateProductionConfig();
        dbConfig = {
          host: process.env.DB_HOST,
          database: process.env.DB_NAME,
          user: process.env.DB_USER,
          password: String(process.env.DB_PASSWORD), // Ensure password is string
          port: parseInt(process.env.DB_PORT, 10),
          ssl: { rejectUnauthorized: false },
        };
      }
      
      return dbConfig;
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
