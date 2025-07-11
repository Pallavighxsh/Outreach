import time
import re
import random
import argparse
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urlparse

EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

def extract_name_and_email(soup):
    emails_data = []
    for tag in soup.find_all(text=re.compile(EMAIL_PATTERN)):
        email = re.search(EMAIL_PATTERN, tag)
        if email:
            email_text = email.group()
            parent = tag.find_parent()
            surrounding_text = parent.get_text(" ", strip=True) if parent else tag.strip()
            name = deduce_name(surrounding_text, email_text)
            emails_data.append((name, email_text))
    return emails_data

def deduce_name(text, email):
    text = text.replace(email, '').strip()
    parts = text.split()
    if 1 <= len(parts) <= 6:
        return text
    return ""

def domain_to_site_name(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return domain.split('.')[0].replace('-', ' ').title()

def scrape_page(url, driver, results):
    print(f"\n🌐 Scraping: {url}")
    wait = WebDriverWait(driver, 15)
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(random.uniform(2, 4))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        site_name = domain_to_site_name(url)
        emails = extract_name_and_email(soup)
        for name, email in emails:
            results.append([name, email, site_name, url])

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")

def write_to_excel(data, file_name="emails_output.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Emails"
    ws.append(["Name", "Email", "Site", "Page URL"])
    for row in data:
        ws.append(row)
    wb.save(file_name)
    print(f"\n✅ Data saved to: {file_name}")

def main():
    parser = argparse.ArgumentParser(description="Scrape names and emails from any webpage.")
    parser.add_argument('--url', nargs='+', required=True, help='One or more URLs to scrape')
    args = parser.parse_args()

    print("🚀 Starting scraper...")
    service = Service("/usr/local/bin/chromedriver")  # Update this path as needed
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=service, options=options)
    results = []

    try:
        for url in args.url:
            scrape_page(url, driver, results)
            time.sleep(random.uniform(2, 5))
    finally:
        driver.quit()
        write_to_excel(results)
        print("\n🛑 Done. Chrome closed.")

if __name__ == "__main__":
    main()
