from datetime import datetime, timedelta, date
import random
from typing import List, Dict
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import logging
import time
import psycopg2
import os
load_dotenv()

# Connection wtih database
conn = psycopg2.connect(
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

# Create a cursor object using the cursor() method
cursor = conn.cursor()



@dataclass
class Fixture: 
    match_id: str
    home_team: str
    away_team: str
    venue: str
    #date is date object, time is string, date_time is timestamp
    date: date
    time: str
    date_time: datetime
    notification_sent_at: datetime


class PremierLeagueScraper:
    def __init__(self, headless:bool=True):
        self.logger = self._setup_logger()
        self.driver = self._setup_driver(headless)
        self.url="https://www.premierleague.com/fixtures"

    def _setup_logger(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger("PremierLeagueScraper")
    
    def _setup_driver(self, headless:bool) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
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


    # Insert into the table
    def insert_into_table(self, fixture, fixture_id):
        """Inserts a fixture into the database."""
        try:
            query = """
            INSERT INTO soccer_2024_pl_fixtures 
            (fixture_id, match_id, home_team, away_team, venue, date, time, date_time, notification_sent_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            cursor.execute(
                query,
                (   
                    fixture_id,
                    fixture.match_id,
                    fixture.home_team,
                    fixture.away_team,
                    fixture.venue,
                    fixture.date,
                    fixture.time,
                    fixture.date_time,
                    None,  # For notification_sent_at
                ),
            )
            conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting into table: {str(e)}")
            conn.rollback()


    def _transformDates(self, date_type, date):
        if date_type == "date_with_time":
            date_format = "%A %d %B %Y %H:%M"
            date_object = datetime.strptime(date, date_format)
            return date_object
        elif date_type == "date_only":
            date_format = "%A %d %B %Y"
            date_object = datetime.strptime(date, date_format)
            return date_object.date()

    def process_date_and_time(self, date, time):
        # Extract kickoff_date (date object)
        kickoff_date = self._transformDates("date_only", date)

        # Retain kickoff_time as a string
        kickoff_time = time

        # Combine date and time for kickoff_date_with_time (datetime object)
        kickoff_date_with_time = self._transformDates("date_with_time", f"{date} {kickoff_time}")

        return kickoff_date, kickoff_time, kickoff_date_with_time

    def _extractFixtures(self):
        try:
            self.logger.info("Extracting fixtures...")
            containers = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "fixtures__date-container"))
            )
            self.logger.info(f"Found {len(containers)} containers")
            for container in containers:
                fixture_id = 'fix_' + str(random.randint(0, 999999)).zfill(6)
                date = container.find_element(By.CLASS_NAME, "fixtures__date--long").text
                fixture_container = container.find_element(By.CLASS_NAME, "fixtures__matches-list")
                matches = fixture_container.find_element(By.CLASS_NAME, "matchList")
                match_items = matches.find_elements(By.TAG_NAME, "li")
                for match in match_items:
                    try:
                        teams = match.find_elements(By.CLASS_NAME, "match-fixture__team-name")
                        home_team = teams[0].find_element(By.CLASS_NAME, "match-fixture__short-name").text
                        away_team = teams[1].find_element(By.CLASS_NAME, "match-fixture__short-name").text
                        home_abbr_name = self.driver.execute_script(
                            "return arguments[0].textContent", 
                            teams[0].find_element(By.CLASS_NAME, "match-fixture__abbr")
                        )
                        away_abbr_name = self.driver.execute_script(
                            "return arguments[0].textContent", 
                            teams[1].find_element(By.CLASS_NAME, "match-fixture__abbr")
                        )
                        kickoff_time = match.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                        kickoff_date, kickoff_time, kickoff_date_with_time = self.process_date_and_time(date, kickoff_time)
                        venue = match.find_element(By.CLASS_NAME, "match-fixture__stadium-name").text
                        match_id = f"{kickoff_date}-{home_abbr_name}-{away_abbr_name}"
                        fixture = Fixture(match_id, home_team, away_team, venue, kickoff_date, kickoff_time, kickoff_date_with_time, None)
                        self.insert_into_table(fixture, fixture_id)

                    except Exception as e:
                        self.logger.error(f"Error extracting match details: {str(e)}")
                        continue
        except Exception as e:
            self.logger.error(f"Error extracting fixtures: {str(e)}")
            return None

    
    def scrape(self) -> List[Fixture]:
        """Main method to scrape fixtures."""
        self.logger.info("Starting scraping process...")
        self.driver.get(self.url)
        self._scrollToBottom()
        self._extractFixtures()
        self.driver.quit()
        self.logger.info("Finished scraping process.")
        
    
def lambda_handler(event, context):
    try: 
        scraper = PremierLeagueScraper(headless=True)
        scraper.scrape()
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': "An error occurred"
        }

if __name__ == "__main__":
    lambda_handler(None, None)
        
