import requests
from bs4 import BeautifulSoup
import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# List of web pages to scrape
web_pages = [
    'https://www.weact.org/latest/events/',
    'https://nyforcleanpower.org/calendar/',
    'https://waterfrontalliance.org/waterfront-events/',
    'https://www.climate.columbia.edu/events',
    'https://www.reticenter.org/events',
    'https://climatemuseum.org/events'
]


def ClimateMuseum_parser(soup):
        # Find the parent div with the specified class
        containers = soup.find_all('div',class_='summary-item summary-item-record-type-event sqs-gallery-design-carousel-slide summary-item-has-thumbnail summary-item-has-excerpt summary-item-has-tags summary-item-has-author summary-item-has-location')

        for container in containers:
            anchors = container.find_all('a', href=True)

        return ['https://climatemuseum.org' + anchor['href'] for anchor in anchors if anchor.has_attr('href')]


def reti_parser(soup):
    # Select all anchors with the specific classes
    anchors = soup.select('a.eventlist-button.sqs-editable-button.sqs-button-element--primary')

    # Extract hrefs from the anchors
    return ['https://www.reticenter.org' + anchor['href'] for anchor in anchors if anchor.has_attr('href')]

def Columbia_parser(soup):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)

    # Navigate to the page
    url = 'https://www.climate.columbia.edu/events'
    driver.get(url)

    # Let the JavaScript load (you can adjust the sleep time if needed)
    time.sleep(2)

    # Get page source
    page_source = driver.page_source

    # Close the browser
    driver.quit()

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all 'a' tags under 'h2' tags
    anchors = soup.select('h2 a')

    return ['https://www.climate.columbia.edu' + anchor['href'] for anchor in anchors if anchor.has_attr('href')]

def NYCleanPower_parser(soup):
    # Find all anchors with class "evcal_col50 dark1 bordr evo_clik_row"
    anchors = soup.select('a.evcal_col50.dark1.bordr.evo_clik_row')

    # Extract hrefs from the anchors that have the href attribute
    return [anchor['href'] for anchor in anchors if anchor.has_attr('href')]

def weact_parser(soup):
    # Find the div with id "future"
    future_div = soup.find('div', id='future')

    # If the div is found, extract hrefs from the anchor tags with class "button button_grey" within it
    return [anchor['href'] for anchor in
            future_div.find_all('a', class_='button button_grey', href=True)] if future_div else []

def waterfront_parser(soup):
    # Find all anchors with the title "View Event Website"
    anchors = soup.find_all('a', attrs={'title': 'View Event Website', 'target': '_blank'})

    # Extract hrefs from the anchors that have the href attribute
    return [anchor['href'] for anchor in anchors if anchor.has_attr('href')]


# Map web pages to their custom parsers
custom_parsers = {
    'https://www.weact.org/latest/events/': weact_parser,
    'https://nyforcleanpower.org/calendar/': NYCleanPower_parser,
    'https://waterfrontalliance.org/waterfront-events/': waterfront_parser,
    'https://www.climate.columbia.edu/events': Columbia_parser,
    'https://www.reticenter.org/events': reti_parser,
    'https://climatemuseum.org/events': ClimateMuseum_parser
    # Add more if needed
}

# Map web pages to their labels and cities
labels_and_cities = {
    'https://www.weact.org/latest/events/': ('weact', 'NYC'),
    'https://nyforcleanpower.org/calendar/': ('NYCleanPower', 'NYC'),
    'https://waterfrontalliance.org/waterfront-events/': ('Waterfront', 'NYC'),
    'https://www.climate.columbia.edu/events': ('Columbia', 'NYC'),
    'https://www.reticenter.org/events': ('Reti', 'NYC'),
    'https://climatemuseum.org/events': ('ClimateMuseum', 'NYC')
    # Add more if needed
}

CSV_HEADER = ['event-href']

OUTPUT_DIR = './CSV_URL_DATA/Climate Tech'  # Change to your desired directory
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

start_time = time.time()
all_urls = []
page_times = []

for index, web_page in enumerate(web_pages):
    page_start_time = time.time()

    print(f"Scraping {web_page} ({index + 1}/{len(web_pages)})...")

    if web_page not in custom_parsers:
        print(f"Error: No custom parser defined for {web_page}")
        continue

    try:
        response = requests.get(web_page, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        urls = custom_parsers[web_page](soup)
        all_urls.extend([(url, web_page) for url in urls])

        page_end_time = time.time()
        elapsed_time = page_end_time - page_start_time
        page_times.append(elapsed_time)
        average_time_per_page = sum(page_times) / len(page_times)
        time_left = average_time_per_page * (len(web_pages) - (index + 1))

        print(f"Extracted {len(urls)} URLs from {web_page}.")
        print(f"Time taken for this page: {elapsed_time:.2f} seconds.")
        print(f"Estimated time left: {int(time_left // 3600)}h {int((time_left % 3600) // 60)}m {int(time_left % 60)}s")

    except Exception as e:
        print(f"Error scraping {web_page}: {e}")

    time.sleep(3)

# Check for duplicates
unique_urls_set = set([url for url, _ in all_urls])
duplicate_count = len(all_urls) - len(unique_urls_set)

print(f"Found {duplicate_count} duplicates.")
print(f"Total unique URLs: {len(unique_urls_set)}")

# Reset (or create) the files before saving unique URLs
for source in labels_and_cities:
    label, city = labels_and_cities[source]
    filename = f"climate_tech_{label}_{city}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(CSV_HEADER)  # Write the header

# Write unique URLs to respective CSV files
for url, source in all_urls:
    if url in unique_urls_set:
        label, city = labels_and_cities[source]
        filename = f"climate_tech_{label}_{city}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'a', newline='') as csvfile:  # Open in append mode
            writer = csv.writer(csvfile)
            writer.writerow([url])
        unique_urls_set.remove(url)  # Remove the URL so it's not saved again

total_time = time.time() - start_time
print(f"Scraping complete in {int(total_time // 3600)}h {int((total_time % 3600) // 60)}m {int(total_time % 60)}s!")