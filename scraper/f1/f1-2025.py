from dataclasses import dataclass
from datetime import datetime, timedelta, date
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time
import psycopg2
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Connection with database
conn = psycopg2.connect(
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
    # database="mike-docker",
    # user="admin",
    # password="admin",
    # host="localhost",
    # port="5431"
)


# Create a cursor object using the cursor() method
cursor = conn.cursor()


@dataclass
class Fixture:
    match_id: str
    round: int
    circuit: str
    date: str
    time: str
    date_time: datetime
    city: str
    race_type: str
    fixture_id: str = None
    notification_sent_at: str = None


class F1Scraper:
    def __init__(self, headless:bool=True):
        self.logger = self._setup_logger()
        self.driver = self._setup_driver(headless)
        self.url = "https://www.formula1.com/en/racing/2025"


    def _setup_logger(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger("F1Scraper")
    

    def _setup_driver(self, headless:bool) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")  # Set window size to ensure elements are visible
        return webdriver.Chrome(options=options)
    
    def _scrollToBottom(self):
        """Scroll to the bottom of the page until no more content loads."""
        self.logger.info("Starting scroll to bottom...")

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        self.logger.info("Finished scrolling to bottom.")


    def _extractIndividualFixture(self, url, fixture_info, race_type):
        try:
            self.logger.info(f"Extracting individual fixture from {url}...")
            self.driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#maincontent"))
            )
            
            # Find the correct row based on the text content
            if race_type == "race":
                # Find the div that contains "Race" text
                row_selector = "//div[contains(@class, 'rounded-md') and contains(@class, 'bg-white')]//span[text()='Race']/ancestor::div[contains(@class, 'rounded-md')]"
            else:
                # Find the div that contains "Qualifying" text
                row_selector = "//div[contains(@class, 'rounded-md') and contains(@class, 'bg-white')]//span[text()='Qualifying']/ancestor::div[contains(@class, 'rounded-md')]"
                
            # Wait for the specific row to be present
            row = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, row_selector))
            )
            
            try:
                # Extract day - it's the first span in the first div
                day_element = row.find_element(By.CSS_SELECTOR, "div.min-w-16.tablet\\:min-w-28 > p > span")
                race_day = day_element.text.strip() if day_element else "Not Found"
                
                # Extract month - it's the span inside the div with bg-lightGray class
                month_element = row.find_element(By.CSS_SELECTOR, "div.min-w-16.tablet\\:min-w-28 > div.bg-lightGray > span")
                race_month = month_element.text.strip() if month_element else "Not Found"
                
                # Extract time - it's the span inside the p tag in the second main div
                time_element = row.find_element(By.CSS_SELECTOR, "div.pl-xs.tablet\\:pl-normal > div > p > span")
                race_time = time_element.text.strip() if time_element else "Not Found"
                race_time = race_time.split("-")[0] if time_element else "Not Found"
                
                # Extract circuit name - this might need adjustment based on the actual page structure
                try:
                    # Looking for the circuit name in the page
                    circuit_element = self.driver.find_element(By.CSS_SELECTOR, ".circuit-name")
                    circuit_name = circuit_element.text.strip() if circuit_element else "Not Found"
                except:
                    circuit_name = f"{fixture_info['country']} Circuit"
                
                # Also try to get city
                try:
                    city_element = self.driver.find_element(By.CSS_SELECTOR, ".circuit-location")
                    city = city_element.text.strip() if city_element else fixture_info['country']
                except:
                    city = fixture_info['country']
                
                # Update fixture info
                fixture_info['race_day'] = race_day
                fixture_info['race_month'] = race_month
                fixture_info['race_time'] = race_time
                fixture_info['race_type'] = "Race" if race_type == "race" else "Qualifying"
                fixture_info['circuit'] = circuit_name
                fixture_info['city'] = city
                
                # self.logger.info(f"Successfully extracted {race_type} details - Day: {race_day}, Month: {race_month}, Time: {race_time}")
                
            except Exception as e:
                self.logger.error(f"Failed to extract {race_type} details: {e}")
                fixture_info['race_day'] = "Not Found"
                fixture_info['race_month'] = "Not Found"
                fixture_info['race_time'] = "Not Found"
                fixture_info['circuit'] = f"{fixture_info['country']} Circuit"
                fixture_info['city'] = fixture_info['country']
            
            # Navigate back to the previous page
            self.driver.back()
            return fixture_info
        
        except Exception as e:
            self.logger.error(f"Failed to extract fixture from {url}: {e}")
            return fixture_info
    
    def _convertMonthToNumber(self, month_name):
        """Convert month name to number."""
        month_dict = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        return month_dict.get(month_name.upper(), 1)
    
    def insertIntoDatabase(self, fixture_info):
        """Insert fixture into database."""
        try:
            # Create match_id
            match_id = f"f1_2025_{fixture_info['round']}_{fixture_info['race_type'].lower()}"
            
            # Parse date components
            day = int(fixture_info.get('race_day', '1'))
            month = self._convertMonthToNumber(fixture_info.get('race_month', 'JAN'))
            year = 2025
            
            # Format date string (e.g., "2025-03-15")
            date_str = f"{year}-{month:02d}-{day:02d}"
            
            # Format time
            time_str = fixture_info.get('race_time', '00:00')
            
            # Combine into datetime
            date_time_str = f"{date_str} {time_str}"
            try:
                date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                # If time format is different, try with just the date
                date_time = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Create a Fixture object
            fixture = Fixture(
                match_id=match_id,
                round=int(fixture_info.get('round', '0').replace('ROUND ', '')),
                circuit=fixture_info.get('circuit', ''),
                date=date_str,
                time=time_str,
                date_time=date_time,
                city=fixture_info.get('city', ''),
                race_type=fixture_info.get('race_type', ''),
                fixture_id=fixture_info.get('fixture_id', '')
            )
            
            # Insert into database
            query = """
            INSERT INTO f1_2025_fixtures 
            (fixture_id, match_id, round, circuit, date, time, date_time, city, race_type) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(
                query,
                (
                    fixture.fixture_id,
                    fixture.match_id,
                    fixture.round,
                    fixture.circuit,
                    fixture.date,
                    fixture.time,
                    fixture.date_time,
                    fixture.city,
                    fixture.race_type,
                ),
            )
            
            conn.commit()
            self.logger.info(f"Successfully inserted {fixture.race_type} for {fixture.circuit}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting into database: {str(e)}")
            conn.rollback()
            return False
    
    def _extractFixtures(self):
        self.logger.info("Extracting fixtures...")
        
        try:
            # Store only the URLs and basic info initially
            fixtures_info = []
            
            # Get initial list of fixtures
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#maincontent > div > div:nth-child(1) > div:nth-child(4)"))
            )
            
            if not container:
                self.logger.error("Container is empty")
                return []
            
            a_tags = container.find_elements(By.TAG_NAME, "a")
            self.logger.info(f"Found {len(a_tags)} fixtures")
            
            # First, collect all URLs and basic info
            for a_tag in a_tags:
                try:
                    round_text = a_tag.find_element(By.CSS_SELECTOR, ".mr-l.pe-xs").text.strip()
                    country = a_tag.find_element(By.CSS_SELECTOR, ".f1-heading").text.strip()
                    url = a_tag.get_attribute("href")
                    
                    fixtures_info.append({
                        "round": round_text,
                        "country": country,
                        "url": url
                    })
                except Exception as e:
                    self.logger.error(f"Error collecting fixture info: {e}")
                    continue
            
            # Now process each fixture URL separately
            all_fixtures = []
            for index, fixture in enumerate(fixtures_info):
                try:
                    self.logger.info(f"Processing fixture {index+1}/{len(fixtures_info)}: {fixture['country']}")
                    
                    # Create fixture info for race
                    race_fixture_info = {
                        "fixture_id": f'fix_{str(random.randint(0, 999999)).zfill(6)}',
                        "round": fixture["round"],
                        "country": fixture["country"]
                    }
                    
                    # Extract race details
                    detailed_fixture_race = self._extractIndividualFixture(fixture["url"], race_fixture_info.copy(), "race")
                    result_race = self.insertIntoDatabase(detailed_fixture_race)
                    if result_race:
                        all_fixtures.append(detailed_fixture_race)
                    
                    # Create new fixture ID for qualifying
                    qualifying_fixture_info = {
                        "fixture_id": f'fix_{str(random.randint(0, 999999)).zfill(6)}',
                        "round": fixture["round"],
                        "country": fixture["country"]
                    }
                    
                    # Extract qualifying details
                    detailed_fixture_qualifying = self._extractIndividualFixture(fixture["url"], qualifying_fixture_info, "qualifying")                    
                    result_qualifying = self.insertIntoDatabase(detailed_fixture_qualifying)
                    if result_qualifying:
                        all_fixtures.append(detailed_fixture_qualifying)
                    
                    # Add a delay to avoid overwhelming the server
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"Error processing fixture {index+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(all_fixtures)} fixtures")
            return all_fixtures
            
        except Exception as e:
            self.logger.error(f"Failed to extract fixtures: {e}")
            return []

    def scrape(self):
        self.logger.info("Starting scrape...")
        try:
            self.driver.get(self.url)
            self._scrollToBottom()
            fixtures = self._extractFixtures()
            self.logger.info(f"Scraped {len(fixtures)} fixtures")
            return fixtures
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            return []
        finally:
            self.driver.quit()
            self.logger.info("Finished scraping process.")


def lambda_handler(event, context):
    try: 
        scraper = F1Scraper(headless=True)
        fixtures = scraper.scrape()
        
        return {
            'statusCode': 200,
            'body': f"Successfully scraped {len(fixtures)} fixtures"
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }

if __name__ == "__main__":
    print("Running locally...")
    result = lambda_handler(None, None)
    print(result)