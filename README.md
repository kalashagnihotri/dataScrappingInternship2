# Twitter Profile Scraper

## Description
This project is a Twitter profile scraper that extracts information from Twitter profiles using Selenium and BeautifulSoup. It automates the process of fetching profile details like name, bio, tweets, followers, and more.

## Features
- Scrapes Twitter profile information
- Extracts name, bio, tweets, followers, and following count
- Uses Selenium for automation
- Uses BeautifulSoup for parsing HTML content

## Prerequisites
Ensure you have the following installed:
- Python 3.x
- Selenium
- BeautifulSoup4
- Google Chrome
- ChromeDriver (compatible with your Chrome version)

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/yourusername/twitter-profile-scraper.git
   cd twitter-profile-scraper
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
1. Update the `chromedriver` path in the script if needed.
2. Run the script:
   ```sh
   python scraper.py
   ```
3. Enter the Twitter profile URL when prompted.
4. View the extracted data in the output.

## Notes
- Twitter may block or limit automated requests, so use delays and avoid frequent scraping.
- You may need to log in manually if Twitter detects automation.



