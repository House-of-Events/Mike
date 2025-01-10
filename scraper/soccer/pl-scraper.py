#Code to scrape the Premier League fixtures from the official website
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Instantiate a Chrome options object
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # Run in headless mode, can remove if you need to see the browser

# Initialize an instance of the Chrome driver in headless mode
driver = webdriver.Chrome(options=options)

# Load the Premier League fixtures page
driver.get("https://www.premierleague.com/fixtures")

# Wait for the initial fixtures to load
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "fixtures__date-container"))
)

# Initialize an array to store fixture data and a set to track seen dates
fixtures_data = []
seen_dates = set()

# Function to collect fixture data (date, teams, time, venue)
def get_fixture_details():
    fixtures = driver.find_elements(By.CLASS_NAME, "fixtures__date-container")
    fixture_details = []

    for fixture in fixtures:
        try:
            # Date of the fixture
            date = fixture.find_element(By.CLASS_NAME, "fixtures__date--long").text
            
            # Skip if the date has already been processed
            if date in seen_dates:
                continue
            seen_dates.add(date)
            
            # Find each match in the fixture container
            matchList = fixture.find_elements(By.CLASS_NAME, "match-fixture")
            for match in matchList:
                # Extract home and away teams
                teams = match.find_elements(By.CLASS_NAME, "match-fixture__team-name")
                if len(teams) >= 2:
                    home_team = teams[0].find_element(By.CLASS_NAME, "match-fixture__short-name").text
                    away_team = teams[1].find_element(By.CLASS_NAME, "match-fixture__short-name").text
                else:
                    home_team = "Unknown Home Team"
                    away_team = "Unknown Away Team"
                
                fixture_details.append((date, home_team, away_team))
                print(date, home_team, away_team)
        except Exception as e:
            # Handle cases where an element might not exist
            print(f"Error extracting fixture details: {e}")


# Scroll and collect new fixture details
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll down
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)  # Wait for the new content to load (adjust as necessary)

    # Wait for more fixtures to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "fixtures__date-container"))
    )
    
    # Collect new fixture details
    get_fixture_details()

    # Check if the page has scrolled completely (if no new content is added)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break

    last_height = new_height

# Quit the browser
driver.quit()

