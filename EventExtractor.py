import pandas as pd
import openai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import time
import datetime
import os
import string

class EventExtractor:
    def __init__(self, api_key, csv_files, column_mapping, city, output_dir=None, num_rows=None):
        openai.api_key = api_key
        self.csv_files = csv_files
        print("csv_files:", self.csv_files)
        self.column_mapping = column_mapping
        print("column_mapping:", self.column_mapping)
        self.city = city
        print("city:", self.city)

        # Default to the current directory if none is given
        if output_dir is None:
            output_dir = os.getcwd()

        whitelist = set(string.ascii_letters + string.digits + '_-')
        sanitized_city = ''.join(c if c in whitelist else '_' for c in city)

        output_filename = f"{sanitized_city}_events_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv"
        self.output_file = os.path.join(output_dir, output_filename)
        print("output_file:", self.output_file)

        print("num_rows:", num_rows)
        self.num_rows = num_rows

    def read_urls_from_csv(self):
        all_urls = []
        all_additional_data = []

        if isinstance(self.num_rows, int):  # if num_rows is a single int, make a list of the same size as csv_files
            num_rows_list = [self.num_rows] * len(self.csv_files)
        elif isinstance(self.num_rows, list):
            if len(self.num_rows) == 1:  # if num_rows is a list of a single int, repeat it for all csv_files
                num_rows_list = self.num_rows * len(self.csv_files)
            elif len(self.num_rows) != len(self.csv_files):
                raise ValueError(
                    "Length of num_rows must equal to the length of csv_files or num_rows must be an integer or a list with a single integer")
            else:
                num_rows_list = self.num_rows
        else:
            raise TypeError("num_rows must be an integer or a list of integers")

        for csv_file, num_rows in zip(self.csv_files, num_rows_list):
            df = pd.read_csv(csv_file)
            if not df.iloc[:, 0].apply(lambda x: bool(urlparse(x).scheme and urlparse(x).netloc)).all():
                print(f"Error: The file {csv_file} does not seem to contain URLs in the first column.")
                continue
            if num_rows == 'MAX' or num_rows == 'MAXALL':
                urls = df.iloc[:, 0].tolist()
                additional_data = df.iloc[:, 1:]
            else:
                urls = df.iloc[:num_rows, 0].tolist()
                additional_data = df.iloc[:num_rows, 1:]

            # Add a column to the additional_data DataFrame with the name of the CSV file
            additional_data['Source CSV'] = csv_file

            all_urls.extend(urls)
            all_additional_data.append(additional_data)

        # Concatenate all additional data
        final_additional_data = pd.concat(all_additional_data)

        # Make 'Source CSV' the first column
        column_order = ['Source CSV'] + [col for col in final_additional_data.columns if col != 'Source CSV']
        final_additional_data = final_additional_data[column_order]

        return all_urls, final_additional_data

    @staticmethod
    def strip_url_parameters(url):
        parsed_url = urlparse(url)
        cleaned_url = urlunparse(parsed_url._replace(query=None))
        return cleaned_url

    @staticmethod
    def extract_body_text(html_content):
        soup = BeautifulSoup(html_content, "lxml")
        body = soup.body
        return body.get_text(separator="\n", strip=True) if body else ""

    def extract_event_details(self, url_content, url):
        prompt_fields = ",".join([f"{value}" for key, value in self.column_mapping.items()])
        prompt = f"""
        Extract the following information from the event webpage content:
        {prompt_fields},
        Use the semicolon character ; to delimit each of the fields.
        The content of the webpage is:

        ---\n{url_content}\n---"""

        while True:
            try:
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
                break
            except openai.error.OpenAIError:
                print("OpenAI API error encountered. Waiting for 30 seconds...")
                time.sleep(30)

        details = response.choices[0]["message"]["content"]
        stripped_url = self.strip_url_parameters(url)

        return details

    @staticmethod
    def write_events_to_csv(events, additional_data, file_path, fields):
        df_output = pd.DataFrame(events)
        n_cols = df_output.shape[1]
        base_cols = list(fields.keys()) + ['Event URL']
        n_base_cols = len(base_cols)
        if n_cols > n_base_cols:
            extra_cols = [f'Extra{c + 1}' for c in range(n_cols - n_base_cols)]
            df_output.columns = base_cols + extra_cols
        else:
            df_output.columns = base_cols
        df_output = pd.concat([df_output, additional_data.reset_index(drop=True)], axis=1)
        df_output.to_csv(file_path, index=False)

    def get_output_file(self):
        # a method to get the value of self.output_file
        return self.output_file

    def run(self, stop_event):
        event_info = []
        urls, additional_data = self.read_urls_from_csv()

        total_urls = len(urls)
        for i, url in enumerate(urls, start=1):
            if stop_event.is_set():
                break
            print(f"Processing URL {i} out of {total_urls}: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            url_content = response.text
            print("Parsing...")
            body_text = self.extract_body_text(url_content)
            print("Sending to GPT...")
            details = self.extract_event_details(body_text, url)
            event_details = [s.replace(';', '\t') for s in details.split(';')]
            event_details.append(self.strip_url_parameters(url))
            print(event_details)
            event_info.append(event_details)

        self.write_events_to_csv(event_info, additional_data, self.output_file, self.column_mapping)
        print(f"The output CSV {self.output_file} has been saved. It contains {len(event_info)} rows.")

