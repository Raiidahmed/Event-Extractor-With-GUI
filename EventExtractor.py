import os
import time
import datetime
import string
from urllib.parse import urlparse, urlunparse

import pandas as pd
import requests
import openai
from bs4 import BeautifulSoup

class EventExtractor:
    def __init__(self, api_key_env, csv_files, column_mapping, city, output_dir=None, num_rows=None):
        """Initializes EventExtractor."""
        openai.api_key = os.environ[api_key_env]

        self.csv_files = csv_files
        self.column_mapping = column_mapping
        self.city = city

        output_dir = os.getcwd() if output_dir is None else output_dir

        whitelist = set(string.ascii_letters + string.digits + '_-')
        sanitized_city = ''.join(c if c in whitelist else '_' for c in self.city)
        output_filename = f"{sanitized_city}_events_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv"

        self.output_file = os.path.join(output_dir, output_filename)
        self.num_rows = num_rows

        print("csv_files: " + ', '.join(os.path.basename(path) for path in self.csv_files))
        print(f"output_file: {os.path.basename(self.output_file)}")
        print(f"num_rows: {num_rows}")

    @staticmethod
    def is_url(value):
        """Checks if the value is a URL."""
        parsed = urlparse(value)
        return bool(parsed.scheme and parsed.netloc)

    def read_urls_from_csv(self):
        """Reads URLs from a CSV file."""
        all_urls = []
        all_additional_data = []

        if isinstance(self.num_rows, int):
            num_rows_list = [self.num_rows] * len(self.csv_files)
        elif isinstance(self.num_rows, list) and len(self.num_rows) == 1:
            num_rows_list = self.num_rows * len(self.csv_files)
        elif isinstance(self.num_rows, list) and len(self.num_rows) == len(self.csv_files):
            num_rows_list = self.num_rows
        else:
            raise TypeError("Invalid num_rows: Must be an int or a list of equal length to csv_files")

        for csv_file, num_rows in zip(self.csv_files, num_rows_list):
            df = pd.read_csv(csv_file)

            if not df.iloc[:, 0].apply(self.is_url).all():
                print(f"Error: {csv_file} does not contain URLs in the first column.")
                continue

            rows = df.iloc[:, 0].tolist() if num_rows in {'MAX', 'MAXALL'} else df.iloc[:num_rows, 0].tolist()
            additional_data = df.iloc[:, 1:] if num_rows in {'MAX', 'MAXALL'} else df.iloc[:num_rows, 1:]
            additional_data['Source CSV'] = csv_file

            all_urls.extend(rows)
            all_additional_data.append(additional_data)

        final_additional_data = pd.concat(all_additional_data)
        column_order = ['Source CSV'] + [col for col in final_additional_data.columns if col != 'Source CSV']
        final_additional_data = final_additional_data[column_order]

        return all_urls, final_additional_data

    @staticmethod
    def strip_url_parameters(url):
        """Removes query parameters from a URL."""
        return urlunparse(urlparse(url)._replace(query=None))

    @staticmethod
    def extract_body_text(html_content):
        """Extracts body text from HTML content."""
        soup = BeautifulSoup(html_content, "lxml")
        body = soup.body
        return body.get_text(separator="\n", strip=True) if body else ""

    def extract_event_details(self, url_content, url):
        """Extracts event details using the OpenAI API."""
        prompt_fields = ",".join(self.column_mapping.values())
        prompt = f"""
        Extract the following information from the event webpage content:
        {prompt_fields},
        Use the semicolon character ; to delimit each of the fields.
        The content of the webpage is:

        ---\n{url_content}\n---"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an event data extractor. All date times should be for year 2023 and should not include timezone. Use a semicolon character ; to delimit different fields extracted. Do not provide field names, just the extracted field.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0]["message"]["content"]

    @staticmethod
    def write_events_to_csv(events, additional_data, file_path, fields):
        """Writes event data to a CSV file."""
        df_output = pd.DataFrame(events)
        base_cols = list(fields.keys()) + ['Event URL']
        if df_output.shape[1] > len(base_cols):
            extra_cols = [f'Extra{c + 1}' for c in range(df_output.shape[1] - len(base_cols))]
            df_output.columns = base_cols + extra_cols
        else:
            df_output.columns = base_cols
        df_output = pd.concat([df_output, additional_data.reset_index(drop=True)], axis=1)
        df_output.to_csv(file_path, index=False)

    def get_output_file(self):
        """Returns the output file path."""
        return self.output_file

    def run(self, stop_event):
        """Runs the event extractor."""
        event_info = []
        urls, additional_data = self.read_urls_from_csv()
        total_urls = len(urls)

        for i, url in enumerate(urls, start=1):
            if stop_event.is_set():
                break
            print(f"Processing URL {i} out of {total_urls}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
            }

            for _ in range(4):  # Will try 4 times before skipping
                try:
                    response = requests.get(url, headers=headers)
                    break
                except requests.exceptions.RequestException:
                    print(f"Error fetching {url}, retrying...")
                    time.sleep(5)  # Optional: Wait for 5 seconds before retrying
            else:  # This will execute if the loop has exhausted all attempts (4 tries in this case) without breaking
                print(f"Failed to fetch {url} after 4 attempts, moving to next URL.")
                continue

            body_text = self.extract_body_text(response.text)
            successful = False  # Create a success flag

            for _ in range(4):  # Will try 4 times before skipping
                try:
                    details = self.extract_event_details(body_text, url)
                    successful = True
                    break  # If successful, we break the loop and do not execute the 'else' clause.
                except openai.error.OpenAIError:
                    print("OpenAI API error encountered. Retrying in 30 seconds...")
                    time.sleep(30)

            if not successful:
                print("Failed to get response from OpenAI after 4 attempts. Moving to next URL.")
                continue  # If OpenAI API failed after 4 attempts, skip to the next URL

            event_details = [s.replace(';', '\t') for s in details.split(';')]
            event_details.append(self.strip_url_parameters(url))
            event_info.append(event_details)

        self.write_events_to_csv(event_info, additional_data, self.output_file, self.column_mapping)
        print(f"The output CSV {self.output_file} has been saved. It contains {len(event_info)} rows.")
