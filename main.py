# I import all the libraries I need.
from selenium import webdriver  # For browser automation
from selenium.webdriver.chrome.service import Service  # To manage the ChromeDriver service
from selenium.webdriver.common.by import By  # To locate elements by various methods
from selenium.webdriver.chrome.options import Options  # To set Chrome options
from bs4 import BeautifulSoup  # To parse HTML
import csv  # To handle CSV files
import time  # For sleep delays
import os  # For path operations and environment variables
import pickle  # To save and load cookies
from dotenv import load_dotenv  # To load environment variables from a .env file
from selenium.webdriver.support.ui import WebDriverWait  # For explicit waits
from selenium.webdriver.support import expected_conditions as EC  # To wait for certain conditions
import mysql.connector  # To connect to MySQL
from mysql.connector import Error  # To catch MySQL errors

# I use webdriver-manager so I don't have to manually manage my ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager

# I load my environment variables from the .env file
load_dotenv()

# I grab my sensitive info (like MySQL credentials and my login details) from the environment
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
# I set the path for saving cookies. Feel free to update this if needed.
COOKIES_PATH = r'C:\src\atutomationScripts\dataScrappingInternship2\dataScrappingInternship2\cookies.pkl'

# I defined this function to initialize my WebDriver.
# (Even though I pass a chromedriver_path here, I later use webdriver-manager for a dynamic path.)
def initialize_driver(chromedriver_path):
    # I set up some Chrome options to make the browser less detectable.
    chrome_options = Options()
    # Uncomment the next line if you want to run Chrome in headless mode.
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")  # Set my user agent
    chrome_options.add_argument("--disable-gpu")  # Disable GPU usage

    # I set up the ChromeDriver service using the provided path.
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # I run this script to hide the fact that I'm using WebDriver.
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# I defined this function to save cookies so I can reuse my login session later.
def save_cookies(driver, path):
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

# I defined this function to load cookies into the browser session.
def load_cookies(driver, path):
    if os.path.exists(path):
        with open(path, "rb") as file:
            cookies = pickle.load(file)
            # I loop through each cookie and adjust its domain before adding it.
            for cookie in cookies:
                cookie["domain"] = ".x.com"  # This makes sure the cookie works on Twitter (X)
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie: {e}")

# I defined this function to log in to Twitter (or X) using my credentials.
def login_to_twitter(driver, email, password):
    # I navigate to the Twitter login page.
    driver.get("https://x.com/login")
    time.sleep(5)  # I give it some time to load.

    # I find the email input field and enter my email.
    email_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="username"]')
    email_input.send_keys(email)
    time.sleep(2)  # Short pause to let the input process

    # I click the "Next" button.
    next_button = driver.find_element(By.XPATH, '//span[text()="Next"]')
    next_button.click()
    time.sleep(5)  # Wait for the next part of the login to load

    # Sometimes Twitter shows a prompt for unusual activity, so I check for that.
    try:
        # I look for the username field that appears in the unusual activity popup.
        username_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="on"][name="text"]')
        print("Unusual activity detected. Entering username...")
        # I extract the username from my email and enter it.
        username = email.split('@')[0]
        username_input.send_keys(username)
        time.sleep(2)
        # I click "Next" again.
        next_button = driver.find_element(By.XPATH, '//span[text()="Next"]')
        next_button.click()
        time.sleep(5)
    except:
        print("No unusual activity detected. Proceeding to password input...")

    # I now find the password field and enter my password.
    password_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="current-password"]')
    password_input.send_keys(password)
    time.sleep(2)

    # I click the "Log in" button.
    login_button = driver.find_element(By.XPATH, '//span[text()="Log in"]')
    login_button.click()
    time.sleep(5)  # Wait for login to complete

    print("Login successful!")

# I defined this function to try logging in with cookies first, and if that fails, fall back to credentials.
def login_with_cookies(driver, email, password, cookies_path):
    driver.get("https://x.com/")
    time.sleep(5)  # Let the page load

    try:
        # I try to load my cookies.
        load_cookies(driver, cookies_path)
        driver.refresh()  # Refresh so cookies take effect
        time.sleep(5)

        # I check if I'm still at the login page.
        if "login" in driver.current_url:
            print("Cookies invalid or expired. Logging in with credentials...")
            login_to_twitter(driver, email, password)
            save_cookies(driver, cookies_path)  # I save new cookies after login.
        else:
            print("Logged in using cookies!")
    except Exception as e:
        print(f"Error loading cookies: {e}. Logging in manually...")
        login_to_twitter(driver, email, password)
        save_cookies(driver, cookies_path)

# I defined this function to scrape the details from a Twitter profile.
# I've added some retry logic in case I get sent back to the login page.
def scrape_twitter_profile(driver, url):
    # I load the profile page.
    driver.get(url)
    time.sleep(5)
    
    # I check if I'm being redirected to login.
    if "login" in driver.current_url or "signin" in driver.page_source:
        print("Login required! Re-authenticating...")
        login_with_cookies(driver, EMAIL, PASSWORD, COOKIES_PATH)
        # I try loading the profile again after logging in.
        driver.get(url)
        time.sleep(5)
        # If I'm still being redirected, I return default values.
        if "login" in driver.current_url or "signin" in driver.page_source:
            return {
                'Bio': 'Login Failed',
                'Location': 'Login Failed',
                'Following Count': 'N/A',
                'Followers Count': 'N/A',
                'Website': 'N/A'
            }

    # I wait until the bio element is present on the page.
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="UserDescription"]'))
        )
    except:
        print("Profile data did not load properly.")
        return {
            'Bio': 'N/A',
            'Location': 'N/A',
            'Following Count': 'N/A',
            'Followers Count': 'N/A',
            'Website': 'N/A'
        }

    # I use BeautifulSoup to parse the page's HTML.
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # I try to extract the bio text.
    try:
        bio = soup.find('div', {'data-testid': 'UserDescription'}).text
    except:
        bio = 'N/A'

    # I try to extract the location.
    try:
        location = soup.find('span', {'data-testid': 'UserLocation'}).text
    except:
        location = 'N/A'

    # I try to extract the following count.
    try:
        following_count = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/following")]//span'))
        ).text
    except:
        following_count = 'N/A'

    # I try to extract the followers count.
    try:
        followers_count = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Followers")]/following-sibling::span'))
        ).text
    except Exception as e:
        print(f"Error extracting followers count: {e}")
        followers_count = 'N/A'

    # I try to extract the website URL.
    try:
        website = soup.find('a', {'data-testid': 'UserUrl'})['href']
    except:
        website = 'N/A'

    # I return all the scraped data as a dictionary.
    return {
        'Bio': bio,
        'Location': location,
        'Following Count': following_count,
        'Followers Count': followers_count,
        'Website': website
    }

# I defined this function to read profile URLs from a CSV file.
def read_profile_urls(csv_path):
    urls = []
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        # I assume the URL is in the first column.
        for row in reader:
            urls.append(row[0])
    return urls

# I defined this function to connect to my MySQL database.
def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        print("Connected to MySQL!")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# I defined this function to insert the scraped data into my MySQL database.
def insert_into_database(data, url):
    connection = None
    try:
        connection = connect_to_mysql()
        if connection:
            cursor = connection.cursor()
            # I prepare my SQL query.
            query = """
            INSERT INTO profiles 
                (bio, location, following_count, followers_count, website, profile_url) 
            VALUES 
                (%s, %s, %s, %s, %s, %s)
            """
            # I create a tuple of values to insert.
            values = (
                data['Bio'],
                data['Location'],
                data['Following Count'],
                data['Followers Count'],
                data['Website'],
                url
            )
            cursor.execute(query, values)
            connection.commit()
            print("Data inserted successfully!")
    except Error as e:
        print(f"Error inserting data: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# This is my main function that ties everything together.
def main():
    # Use webdriver-manager to dynamically initialize ChromeDriver
    service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    # Uncomment the next line if you want to run Chrome in headless mode.
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")  # Set user agent
    chrome_options.add_argument("--disable-gpu")  # Disable GPU usage

    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Dynamically determine the input CSV file path using the current working directory
    current_dir = os.getcwd()
    csv_file_name = "twitter_links.csv"  # Expect the CSV file to be named this
    input_csv_path = os.path.join(current_dir, csv_file_name)

    # Log in to Twitter (X) using cookies or credentials
    login_with_cookies(driver, EMAIL, PASSWORD, COOKIES_PATH)
    
    # Read the profile URLs from the CSV file
    profile_urls = read_profile_urls(input_csv_path)
    scraped_data = []
    
    # Loop through each URL and scrape the profile data
    for url in profile_urls:
        print(f"Scraping: {url}")
        profile_data = scrape_twitter_profile(driver, url)
        scraped_data.append(profile_data)
        
        # Insert the scraped data into the MySQL database
        insert_into_database(profile_data, url)
        
        # Print out the scraped data in the console
        print("Scraped Data:")
        for key, value in profile_data.items():
            print(f"{key}: {value}")
        print("-" * 40)

    # Once done, close the browser
    driver.quit()
    print(f"Scraping completed. Data saved to {MYSQL_DATABASE}")

# Call the main function when the script is executed
if __name__ == "__main__":
    main()
