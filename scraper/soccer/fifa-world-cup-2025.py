import requests
import psycopg2
import os
import logging
import json
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
import random

load_dotenv()

# Database connection
# To use Chamber, either:
# 1. Set CHAMBER_SERVICE=app-aws before running
# 2. Run with: chamber exec app-aws -- python scraper/soccer/fifa-world-cup-2025.py
# 3. Export variables: chamber export app-aws | xargs -I {} export {}

# For local development, use local environment variables
# Run using NODE_ENV=local python3 scraper/soccer/fifa-world-cup-2025.py
# For production, use Chamber environment variables

# Environment detection and configuration
def get_environment_config():
    """Determine environment and set appropriate database configuration."""
    # Check if we're running in a local environment
    is_local = (
        os.getenv("NODE_ENV") == "local" or 
        os.getenv("ENVIRONMENT") == "local" or
        not os.getenv("CHAMBER_SERVICE")  # No Chamber service means local
    )
    
    if is_local:
        print("Running in LOCAL environment")
        # Set local database configuration
        os.environ["DB_HOST"] = "localhost"
        os.environ["DB_PORT"] = "5427"
        os.environ["DB_NAME"] = "mike-docker"
        os.environ["DB_USER"] = "admin"
        os.environ["DB_PASSWORD"] = "admin"
    else:
        print("Running in PRODUCTION/CHAMBER environment")
        # Validate required environment variables for production
        required_env_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_PORT"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

# Initialize environment configuration
get_environment_config()


import psycopg
conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

@dataclass
class Fixture:
    match_id: str
    sport_type: str
    fixture_data: dict
    status: str

class FIFAWorldCup2025Scraper:
    def __init__(self):
        self.logger = self._setup_logger()
        self.api_key = "735fddc2475b72f3209ee0bcf8fedfd0"
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }

    def _setup_logger(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger("FIFAWorldCup2025Scraper")

    def _generate_match_id(self, sport: str, home_team: str, away_team: str, date: str) -> str:
        """Generate a unique match ID."""
        # Extract date part from ISO string
        date_part = date.split('T')[0]
        # Create a simple match ID with sport prefix
        return f"{sport[:3]}-{date_part}-{home_team[:3]}-{away_team[:3]}"

    def _parse_datetime(self, date_string: str) -> tuple:
        """Parse the date string and return date, time, and datetime objects."""
        try:
            # Parse the ISO datetime string
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            
            # Extract date and time components
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%H:%M:%S')
            
            return date_str, time_str, dt
        except Exception as e:
            self.logger.error(f"Error parsing datetime {date_string}: {str(e)}")
            return None, None, None

    def _get_fixture_status(self, status_data: Dict) -> str:
        """Map API status to our database status values."""
        status_mapping = {
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
        }
        
        long_status = status_data.get('long', 'Not Started')
        return status_mapping.get(long_status, 'pending')

    def fetch_fixtures(self, season: str = "2025", league: str = "15") -> List[Dict]:
        """Fetch fixtures from the API."""
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                'season': season,
                'league': league
            }
            
            self.logger.info(f"Fetching fixtures for season {season}, league {league}")
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])
                self.logger.info(f"Successfully fetched {len(fixtures)} fixtures")
                return fixtures
            else:
                self.logger.error(f"API request failed with status code: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching fixtures: {str(e)}")
            return []

    def check_fixture_exists(self, match_id: str) -> bool:
        """Check if a fixture already exists in the database based on match_id."""
        try:
            query = "SELECT COUNT(*) FROM fixtures WHERE match_id = %s"
            cursor.execute(query, (match_id,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking if fixture exists: {str(e)}")
            return False

    def insert_into_table(self, fixture: Fixture):
        """Insert a fixture into the database."""
        try:
            # Check if fixture already exists
            if self.check_fixture_exists(fixture.match_id):
                self.logger.info(f"Fixture with match_id {fixture.match_id} already exists, skipping insertion")
                return
            
            query = """
            INSERT INTO fixtures 
            (match_id, sport_type, fixture_data, status) 
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(
                query,
                (
                    fixture.match_id,
                    fixture.sport_type,
                    json.dumps(fixture.fixture_data),
                    fixture.status,
                ),
            )
            
            result = cursor.fetchone()
            if result:
                self.logger.info(f"Inserted fixture with ID: {result[0]}")
                
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error inserting into table: {str(e)}")
            conn.rollback()

    def process_fixture(self, api_fixture: Dict) -> Fixture:
        """Process a single fixture from the API response."""
        try:
            fixture_data = api_fixture['fixture']
            teams_data = api_fixture['teams']
            league_data = api_fixture['league']
            venue_data = fixture_data.get('venue', {})
            
            # Extract basic data
            home_team = teams_data['home']['name']
            away_team = teams_data['away']['name']
            venue = venue_data.get('name', 'Unknown')
            league = league_data['name']
            
            # Parse datetime
            date_str, time_str, dt = self._parse_datetime(fixture_data['date'])
            if not dt:
                raise ValueError(f"Could not parse datetime: {fixture_data['date']}")
            
            # Generate match_id
            match_id = self._generate_match_id('soccer', home_team, away_team, date_str)
            
            # Get status
            status = self._get_fixture_status(fixture_data['status'])
            
            # Create fixture_data JSONB object
            fixture_data_json = {
                'sport_type': 'soccer',
                'league': league,
                'home_team': home_team,
                'away_team': away_team,
                'venue': venue,
                'date': date_str,
                'time': time_str,
                'date_time': dt.isoformat(),
                'api_fixture_id': str(fixture_data['id']),
                'referee': fixture_data.get('referee'),
                'timezone': fixture_data.get('timezone'),
                'timestamp': fixture_data.get('timestamp'),
                'periods': fixture_data.get('periods'),
                'venue_details': venue_data,
                'status_details': fixture_data.get('status'),
                'teams_details': teams_data,
                'league_details': league_data,
            }
            
            return Fixture(
                match_id=match_id,
                sport_type='soccer',
                fixture_data=fixture_data_json,
                status=status
            )
            
        except Exception as e:
            self.logger.error(f"Error processing fixture: {str(e)}")
            return None

    def scrape(self):
        """Main method to scrape and save fixtures."""
        self.logger.info("Starting FIFA World Cup 2025 scraping process...")
        
        try:
            # Fetch fixtures from API
            fixtures_data = self.fetch_fixtures()
            
            if not fixtures_data:
                self.logger.warning("No fixtures found")
                return
            
            # Process and save each fixture
            for api_fixture in fixtures_data:
                try:
                    fixture = self.process_fixture(api_fixture)
                    if fixture:
                        self.insert_into_table(fixture)
                except Exception as e:
                    self.logger.error(f"Error processing fixture: {str(e)}")
                    continue
            
            self.logger.info("Finished FIFA World Cup 2025 scraping process.")
            
        except Exception as e:
            self.logger.error(f"Error in scraping process: {str(e)}")

def lambda_handler(event, context):
    try:
        scraper = FIFAWorldCup2025Scraper()
        scraper.scrape()
        
        return {
            'statusCode': 200,
            'body': "FIFA World Cup 2025 fixtures scraped successfully"
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }

if __name__ == "__main__":
    lambda_handler(None, None) 