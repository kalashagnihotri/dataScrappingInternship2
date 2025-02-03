from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import csv
import time
import os
import pickle
from dotenv import load_dotenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables from .env file
load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
COOKIES_PATH = r'C:\src\atutomationScripts\dataScrappingInternship2\cookies.pkl'  # Path to save cookies

# Function to initialize the WebDriver in headless mode
def initialize_driver(chromedriver_path):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36") # Set a custom user agent
    chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode
    service = Service(chromedriver_path)  # Path to your ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") # Bypass bot detection
    return driver

# Function to save cookies
def save_cookies(driver, path):
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

# Function to load cookies
def load_cookies(driver, path):
    if os.path.exists(path):
        with open(path, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                # Ensure the domain matches Twitter's domain
                cookie["domain"] = ".x.com"
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie: {e}")

# Function to log in to Twitter
def login_to_twitter(driver, email, password):
    # Navigate to Twitter login page
    driver.get("https://x.com/login")
    time.sleep(5)  # Wait for the page to load

    # Enter email
    email_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="username"]')
    email_input.send_keys(email)
    time.sleep(2)  # Wait for input to be processed

    # Click "Next" button
    next_button = driver.find_element(By.XPATH, '//span[text()="Next"]')
    next_button.click()
    time.sleep(5)  # Wait for the next page to load

    # Check if unusual activity pop-up appears
    try:
        # Look for the username input field (indicates unusual activity pop-up)
        username_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="on"][name="text"]')
        print("Unusual activity detected. Entering username...")

        # Enter username (extracted from email)
        username = email.split('@')[0]  # Extract username from email
        username_input.send_keys(username)
        time.sleep(2)  # Wait for input to be processed

        # Click "Next" button again
        next_button = driver.find_element(By.XPATH, '//span[text()="Next"]')
        next_button.click()
        time.sleep(5)  # Wait for the next page to load
    except:
        print("No unusual activity detected. Proceeding to password input...")

    # Enter password
    password_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="current-password"]')
    password_input.send_keys(password)
    time.sleep(2)  # Wait for input to be processed

    # Click "Log in" button
    login_button = driver.find_element(By.XPATH, '//span[text()="Log in"]')
    login_button.click()
    time.sleep(5)  # Wait for login to complete

    print("Login successful!")

# Function to log in with cookies or fallback to credentials
def login_with_cookies(driver, email, password, cookies_path):
    driver.get("https://x.com/")
    time.sleep(5)  # Let the page load

    # Try loading cookies before login attempt
    try:
        load_cookies(driver, cookies_path)
        driver.refresh()
        time.sleep(5)  # Wait for cookies to take effect

        # Check if login is still required
        if "login" in driver.current_url:
            print("Cookies invalid or expired. Logging in with credentials...")
            login_to_twitter(driver, email, password)
            save_cookies(driver, cookies_path)
        else:
            print("Logged in using cookies!")
    except Exception as e:
        print(f"Error loading cookies: {e}. Logging in manually...")
        login_to_twitter(driver, email, password)
        save_cookies(driver, cookies_path)

# Function to scrape Twitter profile details
def scrape_twitter_profile(driver, url):
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Check if redirected to login page
    if "login" in driver.current_url or "signin" in driver.page_source:
        print(f"Twitter redirected to login! Unable to scrape {url}")
        return {
            'Bio': 'Login Required',
            'Location': 'Login Required',
            'Following Count': 'N/A',
            'Followers Count': 'N/A',
            'Website': 'N/A'
        }

    # Wait for the profile data to load
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

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract Bio
    try:
        bio = soup.find('div', {'data-testid': 'UserDescription'}).text
    except:
        bio = 'N/A'

    # Extract Location
    try:
        location = soup.find('span', {'data-testid': 'UserLocation'}).text
    except:
        location = 'N/A'

    # Extract Following Count
    try:
        following_count = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/following")]//span'))
        ).text
    except:
        following_count = 'N/A'

    # Extract Followers Count
    try:
        followers_count = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Followers")]/following-sibling::span'))
    ).text
    except Exception as e:
        print(f"Error extracting followers count: {e}")
    followers_count = 'N/A'

    # Extract Website
    try:
        website = soup.find('a', {'data-testid': 'UserUrl'})['href']
    except:
        website = 'N/A'

    return {
        'Bio': bio,
        'Location': location,
        'Following Count': following_count,
        'Followers Count': followers_count,
        'Website': website
    }

# Function to read Twitter profile URLs from a CSV file
def read_profile_urls(csv_path):
    urls = []
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            urls.append(row[0])  # Assuming URLs are in the first column
    return urls

# Function to write scraped data to a new CSV file
def write_to_csv(data, output_csv_path):
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

# Main function
def main():
    # Path to your ChromeDriver
    chromedriver_path = r'C:\src\things\chromedriver-win64\chromedriver-win64\chromedriver.exe'  # Replace with your ChromeDriver path

    # Path to the input CSV containing Twitter profile URLs
    input_csv_path = r'C:\src\atutomationScripts\dataScrappingInternship2\twitter_links.csv'  # Replace with your input CSV path

    # Path to the output CSV where scraped data will be saved
    output_csv_path = r'C:\src\atutomationScripts\dataScrappingInternship2\output_twitter_links.csv'  # Replace with your desired output CSV path

    # Initialize the WebDriver
    driver = initialize_driver(chromedriver_path)

    # Log in to Twitter using cookies or credentials
    login_with_cookies(driver, EMAIL, PASSWORD, COOKIES_PATH)

    # Read Twitter profile URLs from the input CSV
    profile_urls = read_profile_urls(input_csv_path)

    # Scrape data from each profile
    scraped_data = []
    for url in profile_urls:
        print(f"Scraping: {url}")
        profile_data = scrape_twitter_profile(driver, url)
        scraped_data.append(profile_data)

        # Print the scraped data to the terminal
        print("Scraped Data:")
        for key, value in profile_data.items():
            print(f"{key}: {value}")
        print("-" * 40)

    # Write the scraped data to the output CSV
    write_to_csv(scraped_data, output_csv_path)

    # Close the WebDriver
    driver.quit()

    print(f"Scraping completed. Data saved to {output_csv_path}")

# Run the script
if __name__ == "__main__":
    main()

