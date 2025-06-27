import { execSync } from 'child_process';

// Get secrets from Chamber
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

const appSecrets = getChamberSecrets('app-aws');

export default {
    // Database Configuration
    DB_HOST: appSecrets.db_host || 'localhost',
    DB_PORT: parseInt(appSecrets.db_port) || 5432,
    DB_NAME: appSecrets.db_name || 'fixtures_daily',
    DB_USER: appSecrets.db_username || 'postgres', 
    DB_PASSWORD: appSecrets.db_password || 'postgres',
    
    // SSL Configuration - Enable SSL for development environment
    DB_SSL: true,
    SHADOW_DB_SSL: true,
};