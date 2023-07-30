import os
import requests
from bs4 import BeautifulSoup
import csv
import time

# Base URL without city and term
URL_TEMPLATE = "https://www.eventbrite.com/d/{city}/{term}/?page="

# Set your desired output directory here
OUTPUT_DIR = "./CSV_URL_DATA/Climate Tech"

'''OUTPUT_DIR = "./CSV_URL_DATA/AI Governance"'''

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def ensure_directory_exists(directory):
    """Ensure that the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def seconds_to_hms(seconds):
    """Convert seconds to hours, minutes, seconds."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def get_event_links(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        events = soup.select('.horizontal-event-card__action-visibility .Stack_root__1ksk7 a')
        return [event['href'] for event in events if event.has_attr('href')]
    except requests.RequestException as e:
        print(f"Request error for {url}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error when processing {url}: {e}")
        return []

def generate_filename(city, term):
    city_abbreviation_mapping = {
        "england--london": "London",
        "ca--los-angeles": "LA",
        "dc--washington": "DC",
        "il--chicago": "Chicago",
        "netherlands--amsterdam": "Amsterdam",
        "ny--new-york": "NYC",
        "singapore--singapore": "Singapore",
        "ca--san-francisco": "SF",
        "wa--seattle": "Seattle",
        "ma--boston": "Boston",
        "canada--montreal": "MTL",
    }
    filename = f"climate_tech_eventbrite_{term}_{city_abbreviation_mapping[city]}.csv"

    '''filename = f"AI_Governance_eventbrite_{term}_{city_abbreviation_mapping[city]}.csv"'''

    return os.path.join(OUTPUT_DIR, filename)

def save_to_csv(data, city, term):
    try:
        filename = generate_filename(city, term)
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["event-href"])
            for link in data:
                writer.writerow([link])
    except IOError as e:
        print(f"File error: {e}")
    except Exception as e:
        print(f"Unexpected error when saving to CSV: {e}")

def main():
    # Ensure the output directory exists
    ensure_directory_exists(OUTPUT_DIR)

    cities = [
        "england--london",
        "ca--los-angeles",
        "dc--washington",
        "il--chicago",
        "netherlands--amsterdam",
        "ny--new-york",
        "singapore--singapore",
        "ca--san-francisco",
        "wa--seattle",
        "ma--boston",
        "canada--montreal"
    ]

    '''cities = ["ny--new-york"]'''

    terms = ["climate", "sustainability", "environment"]

    '''terms = ["AI Ethics", "AI Governance", "Social AI"]'''

    total_combinations = len(cities) * len(terms)
    completed_combinations = 0

    all_links = []
    links_per_combination = {}

    start_time = time.time()

    for city in cities:
        for term in terms:
            base_url = URL_TEMPLATE.format(city=city, term=term)
            specific_links = []  # store links for this specific city and term
            for page_num in range(1, 6):
                current_url = base_url + str(page_num)
                event_links = get_event_links(current_url)
                specific_links.extend(event_links)
                all_links.extend(event_links)
                print(f"Scraped {len(event_links)} links from {city} for term '{term}' on page {page_num}")

            links_per_combination[(city, term)] = specific_links

            completed_combinations += 1
            elapsed_time = time.time() - start_time
            avg_time_per_combination = elapsed_time / completed_combinations
            remaining_combinations = total_combinations - completed_combinations
            estimated_time_remaining = avg_time_per_combination * remaining_combinations

            # Modified printing for time
            elapsed_time_str = seconds_to_hms(time.time() - start_time)
            estimated_time_remaining_str = seconds_to_hms(estimated_time_remaining)

            print(f"\nElapsed time: {elapsed_time_str}")
            print(f"Estimated time remaining: {estimated_time_remaining_str}\n")

    print(f"\nTotal links scraped: {len(all_links)}")
    unique_links = set(all_links)  # Convert list to set to remove duplicates
    print(f"Number of duplicate links: {len(all_links) - len(unique_links)}")

    for (city, term), links in links_per_combination.items():
        print(f"\nSaving links for city '{city}' term '{term}' to CSV...")
        save_to_csv(links, city, term)

    print("\nAll links saved successfully!")


if __name__ == '__main__':
    main()
