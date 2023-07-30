import csv
import psycopg2
from urllib.parse import urlparse, urlunparse
import tkinter as tk
from tkinter import filedialog
import os

OUTPUT_DIR = "./Cleaned_CSV_URL_DATA/Climate Tech"

'''OUTPUT_DIR = "./Cleaned_CSV_URL_DATA/AI Governance"'''

def clean_url(url):
    """Remove parameters from a URL."""
    parsed = urlparse(url)
    return urlunparse([parsed.scheme, parsed.netloc, parsed.path, "", "", ""])

def is_valid_url(url):
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_existing_urls_from_db(conn):
    """Fetch existing URLs from the PostgreSQL database."""
    cur = conn.cursor()
    cur.execute("SELECT event_url FROM events;")
    return {row[0] for row in cur.fetchall()}

def process_files(files):
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname='CTC_Events_DB',
        user='Raiidahmed',
        password='Kidsoftheblackhole!3700',
        host='ctc-events.chdn12vvjsde.us-east-2.rds.amazonaws.com',
        port='5432'
    )

    '''conn = psycopg2.connect(
        dbname='ai_events_DB',
        user='Raiidahmed',
        password='Matanui123A!~',
        host='ai-events.chdn12vvjsde.us-east-2.rds.amazonaws.com',
        port='5432'
    )'''

    existing_urls = get_existing_urls_from_db(conn)
    conn.close()

    total_duplicate_urls = 0
    all_urls = set()  # Consolidated set of all URLs

    for input_file in files:
        with open(input_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            urls = [row[0] for row in reader if is_valid_url(row[0])]

            clean_urls = set()
            for url in urls:
                print(f"Checking URL: {url}")
                cleaned = clean_url(url)
                if cleaned in existing_urls or cleaned in clean_urls:
                    print(f"Duplicate URL found: {cleaned}")
                    total_duplicate_urls += 1
                else:
                    clean_urls.add(cleaned)
                    all_urls.add(cleaned)  # Add the cleaned URL to the consolidated set

            # Write to new CSV file
            output_file = "cleaned_" + input_file.split("/")[-1]
            output_path = os.path.join(OUTPUT_DIR, output_file)
            with open(output_path, 'w') as out_f:
                writer = csv.writer(out_f)
                writer.writerow(headers)
                for url in clean_urls:
                    writer.writerow([url])

    print(f"Total duplicate URLs found: {total_duplicate_urls}")

    # Write all URLs to a consolidated CSV
    '''with open("all_cleaned_urls.csv", 'w') as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["URL"])  # header
        for url in all_urls:
            writer.writerow([url])'''

def browse_files():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_paths = filedialog.askopenfilenames(title="Select CSV files", filetypes=[("CSV files", "*.csv")])
    process_files(file_paths)

if __name__ == "__main__":
    browse_files()
