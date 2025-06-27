import axios from 'axios';
import pkg from 'pg';
const { Client } = pkg;
import config from '../../config/index.js';

class FIFAWorldCup2025Scraper {
  constructor() {
    this.apiKey = "735fddc2475b72f3209ee0bcf8fedfd0";
    this.baseUrl = "https://v3.football.api-sports.io";
    this.headers = {
      'x-rapidapi-host': 'v3.football.api-sports.io',
      'x-rapidapi-key': this.apiKey
    };
    
    // Initialize database client
    this.dbClient = new Client({
      host: config.DB_HOST,
      port: config.DB_PORT,
      database: config.DB_NAME,
      user: config.DB_USER,
      password: config.DB_PASSWORD,
      ssl: this.getSSLConfig()
    });
  }

  // Get SSL configuration based on environment
  getSSLConfig() {
    // For development/production environments, typically need SSL
    if (process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'production') {
      return {
        rejectUnauthorized: false // Allow self-signed certificates
      };
    }
    
    // For local development, usually no SSL needed
    if (process.env.NODE_ENV === 'local') {
      return false;
    }
    
    // Default to requiring SSL for unknown environments
    return {
      rejectUnauthorized: false
    };
  }

  // Generate unique match ID
  generateMatchId(sport, homeTeam, awayTeam, date) {
    const datePart = date.split('T')[0];
    return `${sport.substring(0, 3)}-${datePart}-${homeTeam.substring(0, 3)}-${awayTeam.substring(0, 3)}`;
  }

  // Parse datetime string
  parseDateTime(dateString) {
    try {
      const dt = new Date(dateString);
      const date = dt.toISOString().split('T')[0];
      const time = dt.toISOString().split('T')[1].split('.')[0];
      return { date, time, datetime: dt.toISOString() };
    } catch (error) {
      console.error(`Error parsing datetime ${dateString}:`, error.message);
      return null;
    }
  }

  // Map API status to database status
  getFixtureStatus(statusData) {
    const statusMapping = {
      'Match Finished': 'completed',
      'Match Postponed': 'delayed',
      'Match Cancelled': 'cancelled',
      'Match Suspended': 'delayed',
      'Match Delayed': 'delayed',
      'Not Started': 'pending',
      'Halftime': 'pending',
      'Second Half Started': 'pending',
      'Extra Time': 'pending',
      'Break Time': 'pending',
      'Penalty In Progress': 'pending',
      'Match Abandoned': 'cancelled',
      'Match Not Finished': 'delayed'
    };
    
    const longStatus = statusData?.long || 'Not Started';
    return statusMapping[longStatus] || 'pending';
  }

  // Fetch fixtures from API
  async fetchFixtures(season = "2025", league = "15") {
    try {
      console.log(`Fetching fixtures for season ${season}, league ${league}`);
      
      const response = await axios.get(`${this.baseUrl}/fixtures`, {
        headers: this.headers,
        params: { season, league }
      });

      if (response.status === 200) {
        const fixtures = response.data?.response || [];
        console.log(`Successfully fetched ${fixtures.length} fixtures`);
        return fixtures;
      } else {
        console.error(`API request failed with status code: ${response.status}`);
        return [];
      }
    } catch (error) {
      console.error('Error fetching fixtures:', error.message);
      return [];
    }
  }

  // Check if fixture exists in database
  async checkFixtureExists(matchId) {
    try {
      const query = 'SELECT COUNT(*) FROM fixtures WHERE match_id = $1';
      const result = await this.dbClient.query(query, [matchId]);
      return parseInt(result.rows[0].count) > 0;
    } catch (error) {
      console.error('Error checking if fixture exists:', error.message);
      return false;
    }
  }

  // Insert fixture into database
  async insertFixture(fixture) {
    try {
      // Check if fixture already exists
      if (await this.checkFixtureExists(fixture.matchId)) {
        console.log(`Fixture with match_id ${fixture.matchId} already exists, skipping insertion`);
        return;
      }

      const query = `
        INSERT INTO fixtures 
        (match_id, sport_type, fixture_data, status, date_time) 
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
      `;

      const result = await this.dbClient.query(query, [
        fixture.matchId,
        fixture.sportType,
        JSON.stringify(fixture.fixtureData),
        fixture.status,
        fixture.dateTime
      ]);

      if (result.rows.length > 0) {
        console.log(`Inserted fixture with ID: ${result.rows[0].id}`);
      }
    } catch (error) {
      console.error('Error inserting fixture:', error.message);
    }
  }

  // Process single fixture from API response
  processFixture(apiFixture) {
    try {
      const fixtureData = apiFixture.fixture;
      const teamsData = apiFixture.teams;
      const leagueData = apiFixture.league;
      const venueData = fixtureData.venue || {};

      // Extract basic data
      const homeTeam = teamsData.home.name;
      const awayTeam = teamsData.away.name;
      const venue = venueData.name || 'Unknown';
      const league = leagueData.name;

      // Parse datetime
      const dateTime = this.parseDateTime(fixtureData.date);
      if (!dateTime) {
        throw new Error(`Could not parse datetime: ${fixtureData.date}`);
      }

      // Generate match ID
      const matchId = this.generateMatchId('soccer', homeTeam, awayTeam, dateTime.date);

      // Get status
      const status = this.getFixtureStatus(fixtureData.status);

      // Create fixture data object
      const fixtureDataJson = {
        sport_type: 'soccer',
        league,
        home_team: homeTeam,
        away_team: awayTeam,
        venue,
        date: dateTime.date,
        time: dateTime.time,
        date_time: dateTime.datetime,
        api_fixture_id: fixtureData.id.toString(),
        referee: fixtureData.referee,
        timezone: fixtureData.timezone,
        timestamp: fixtureData.timestamp,
        periods: fixtureData.periods,
        venue_details: venueData,
        status_details: fixtureData.status,
        teams_details: teamsData,
        league_details: leagueData
      };

      return {
        matchId,
        sportType: 'soccer',
        fixtureData: fixtureDataJson,
        status,
        dateTime: dateTime.datetime
      };
    } catch (error) {
      console.error('Error processing fixture:', error.message);
      return null;
    }
  }

  // Connect to database with retry logic
  async connectToDatabase() {
    const maxRetries = 3;
    let retries = 0;
    
    while (retries < maxRetries) {
      try {
        console.log(`Attempting to connect to database (attempt ${retries + 1}/${maxRetries})...`);
        console.log(`Host: ${config.DB_HOST}, Port: ${config.DB_PORT}, Database: ${config.DB_NAME}, User: ${config.DB_USER}`);
        
        await this.dbClient.connect();
        console.log('Successfully connected to database');
        return;
      } catch (error) {
        retries++;
        console.error(`Database connection attempt ${retries} failed:`, error.message);
        
        if (retries >= maxRetries) {
          throw new Error(`Failed to connect to database after ${maxRetries} attempts: ${error.message}`);
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }

  // Main scraping method
  async scrape() {
    console.log('Starting FIFA World Cup 2025 scraping process...');

    try {
      // Connect to database
      await this.connectToDatabase();

      // Fetch fixtures from API
      const fixturesData = await this.fetchFixtures();

      if (fixturesData.length === 0) {
        console.log('No fixtures found');
        return;
      }

      // Process and save each fixture
      for (const apiFixture of fixturesData) {
        try {
          const fixture = this.processFixture(apiFixture);
          if (fixture) {
            await this.insertFixture(fixture);
          }
        } catch (error) {
          console.error('Error processing fixture:', error.message);
          continue;
        }
      }

      console.log('Finished FIFA World Cup 2025 scraping process.');
    } catch (error) {
      console.error('Error in scraping process:', error.message);
    } finally {
      // Close database connection
      await this.dbClient.end();
      console.log('Database connection closed');
    }
  }
}

// Lambda handler for AWS Lambda
export const lambdaHandler = async (event, context) => {
  try {
    const scraper = new FIFAWorldCup2025Scraper();
    await scraper.scrape();

    return {
      statusCode: 200,
      body: JSON.stringify("FIFA World Cup 2025 fixtures scraped successfully")
    };
  } catch (error) {
    console.error('Lambda handler error:', error.message);
    return {
      statusCode: 500,
      body: JSON.stringify(`An error occurred: ${error.message}`)
    };
  }
};

// Main execution for local testing
const main = async () => {
  const scraper = new FIFAWorldCup2025Scraper();
  await scraper.scrape();
};

// Run if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}


// Run locally - NODE_ENV=local node scraper/soccer/fifa-club-world-cup-2025.js
// Run in production - NODE_ENV=development node scraper/soccer/fifa-club-world-cup-2025.js