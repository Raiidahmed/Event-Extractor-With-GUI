import os
import time
import string
from urllib.parse import urlparse, urlunparse
import pandas as pd
import openai
import dateparser
import math
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class PastDateError(Exception):
    """Raised when the date is in the past."""
    pass

class AddressParseError(Exception):
    """Raised when the address parsing fails."""
    pass

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
        output_filename = f"{sanitized_city}_events_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv"

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
        all_data = []

        if isinstance(self.num_rows, int):
            num_rows_list = [self.num_rows] * len(self.csv_files)
        elif isinstance(self.num_rows, list) and len(self.num_rows) == 1:
            num_rows_list = self.num_rows * len(self.csv_files)
        elif isinstance(self.num_rows, list) and len(self.num_rows) == len(self.csv_files):
            num_rows_list = self.num_rows
        else:
            raise TypeError("Invalid num_rows: Must be an int or a list of equal length to csv_files")

        for csv_file, num_rows in zip(self.csv_files, num_rows_list):
            if num_rows == 'MAX':
                df = pd.read_csv(csv_file)
            else:
                df = pd.read_csv(csv_file, nrows=num_rows)

            # If df is a Series (happens when the CSV has only one row), convert it to a DataFrame
            if isinstance(df, pd.Series):
                df = df.to_frame().transpose()

            # Replace NaN values with an empty string
            df.iloc[:, 0].fillna('', inplace=True)

            if not df.iloc[:, 0].apply(self.is_url).all():
                print(f"Error: {csv_file} does not contain URLs in the first column.")
                continue

            df['City'] = str(csv_file).rsplit('_', 1)[-1].replace('.csv', '')
            df['Source CSV'] = csv_file

            all_data.append(df)

        final_data = pd.concat(all_data)
        final_data.reset_index(drop=True, inplace=True)

        # Drop duplicate URLs here after all dataframes have been concatenated
        final_data.drop_duplicates(subset=final_data.columns[0], keep='first', inplace=True)

        all_urls = final_data.iloc[:, 0].tolist()
        final_additional_data = final_data.iloc[:, 1:]

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

    @staticmethod
    def parse_dates(event_details, datetime_fields):
        current_datetime = datetime.now()

        for i in datetime_fields:
            date_string = event_details[i]
            parsed_date = dateparser.parse(date_string)
            if parsed_date is None:
                raise ValueError(f"Failed to parse date: {date_string}")
            if parsed_date < current_datetime:
                raise PastDateError(f"Skipping event due to date {parsed_date} occurring in the past")
            # Replace the original string with the standardized datetime string
            event_details[i] = parsed_date.strftime('%B %d, %Y, %I:%M %p')

        return event_details

    @staticmethod
    def parse_addresses(event_details, address_fields):
        address_string = event_details[address_fields]

        address_parts = address_string.split(" ")

        if len(address_parts) < 5 and "Online" not in address_string:
            raise AddressParseError(f"Failed to parse address: {address_string}")

        event_details[address_fields] = address_string

        return event_details

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
                    "content": "You are an event data extractor. All date times should not include timezone. Use a semicolon character ; to delimit different fields extracted. Do not provide field names, just the extracted field.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0]["message"]["content"]

    @staticmethod
    def write_events_to_csv(events, additional_data, file_path, fields):
        """Writes event data to a CSV file."""
        df_output = pd.DataFrame(events)
        base_cols = list(fields.keys()) + ['Event URL'] + ['Relevance']
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

    @staticmethod
    def check_relevance(dataframe, terms, max_prompts_per_request=25):
        """
        Method to read input prompts from the dataframe and check their relevance against a list of terms using the GPT API.
        The method appends the relevance result to the dataframe.

        Parameters:
            terms (list[str]): List of terms against which relevance of the input strings is to be checked.
            max_prompts_per_request (int): Maximum number of input strings to be checked in a single API request.
        """
        term_string = ', '.join(terms)
        input_prompts = [row[0] for row in dataframe]
        num_prompts = len(input_prompts)
        num_requests = math.ceil(num_prompts / max_prompts_per_request)

        # Prepare a list to hold the relevance results
        relevance_results = []

        print("Starting the relevance check process...\n")

        for i in range(num_requests):
            retries = 0

            while retries < 10:
                try:
                    start = i * max_prompts_per_request
                    end = min((i + 1) * max_prompts_per_request, num_prompts)
                    batch_prompts = input_prompts[start:end]

                    # Prepare the prompt string with all batch prompts included
                    batch_prompts_string = "\n---\n".join(batch_prompts)
                    prompt_string = f"""
                    For each of the following texts, give a single TRUE/FALSE value if it relates to even a single one of the following terms: {term_string}.
                    THERE ARE {len(batch_prompts)} INPUTS, SO THERE SHOULD BE {len(batch_prompts)} OUTPUTS!
                    The texts are:

                    ---\n{batch_prompts_string}\n---"""

                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a relevance checker. Use a semicolon character ; to delimit different fields extracted. Do not provide field names, just the extracted field.",
                            },
                            {"role": "user", "content": prompt_string},
                        ],
                    )

                    # Print out the model's response
                    print(f"Response for batch {i + 1}:\n{response.choices[0]['message']['content']}\n")

                    # Split the model's response by the semicolon character and remove leading/trailing whitespace
                    batch_results = [res.strip() for res in response.choices[0]["message"]["content"].split(';')]

                    if len(batch_results) != len(batch_prompts):
                        raise ValueError(
                            "Received a different number of results than expected. Please check the model's responses.")

                    relevance_results.extend([result.lower() == 'true' for result in batch_results])

                    print(f"Iteration {i + 1} of {num_requests} completed successfully.")
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error in iteration {i + 1}: {e}. Retry {retries} of 10.")
                    time.sleep(2)  # Optional: sleep for 2 seconds before retrying
                    if retries == 10:
                        print("Maximum retries exceeded. Breaking the loop.")
                        return

        # Append the results to the dataframe
        print("Relevance check process completed.")
        return(relevance_results)

    def process_url_with_bs(self, url):
        """Processes a URL with BeautifulSoup."""
        for _ in range(3):
            try:

                r = requests.get(url)
                html_content = r.content

                soup = BeautifulSoup(html_content, 'html.parser')

                # Find the specific h1 with the class
                h1 = soup.find('h1', class_='event-title css-0')

                # Find the specific meta tag with the property event:start_time
                start_time_meta = soup.find('meta', property=lambda x: x == 'event:start_time' if x else False)

                # Get the content within that meta tag
                start_time_str = start_time_meta['content']

                # Parse the string into a datetime object
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))

                # Find the specific meta tag with the property event:end_time
                end_time_meta = soup.find('meta', property=lambda x: x == 'event:end_time' if x else False)

                # Get the content within that meta tag
                end_time_str = end_time_meta['content']

                # Parse the string into a datetime object
                end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))

                # Find the specific meta tag with the name twitter:data1
                location_meta = soup.find('meta', attrs={'name': 'twitter:data1'})

                # Get the value within that meta tag
                location = location_meta['value']

                description = soup.find('div', class_='has-user-generated-content')

                organizer = soup.find('a', class_='descriptive-organizer-info__name-link')


                return [h1.get_text(), start_time.strftime('%B %d, %Y, %I:%M %p'),
                        end_time.strftime('%B %d, %Y, %I:%M %p'), location, description.get_text(), organizer['href']]

            except Exception as e:
                print(f"Error processing URL with BeautifulSoup: {url}. Error: {e}")
        else:
            print(f"Failed to process URL with BeautifulSoup after 3 attempts: {url}")
            return None

    def run(self, stop_event):
        """Runs the event extractor."""
        event_info = []
        urls, additional_data = self.read_urls_from_csv()
        total_urls = len(urls)
        datetime_fields = {1, 2}  # indices of datetime fields in event_details
        address_fields = 3

        for i, url in enumerate(urls, start=1):
            if stop_event.is_set():
                break
            print(f"Processing URL {i} out of {total_urls}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
            }

            for _ in range(10):  # Will try 4 times before skipping
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    break
                except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                    print(f"Error fetching {url}, retrying...")
                    time.sleep(5)  # Optional: Wait for 5 seconds before retrying
            else:  # This will execute if the loop has exhausted all attempts (4 tries in this case) without breaking
                print(f"Failed to fetch {url} after 10 attempts, moving to next URL.")
                continue

            body_text = self.extract_body_text(response.text)
            event_details = []

            soup_flag = False

            if "eventbrite.com" in url:
                print(f'Attempting to process URL {i} with Beautiful Soup')
                event_details = self.process_url_with_bs(url)
                if event_details != None:
                    event_details.append(self.strip_url_parameters(url))
                    soup_flag = True
                else:
                    soup_flag = 'SHIFT'

            if soup_flag == False or soup_flag == 'SHIFT':
                print(f'Processing URL {i} with GPT')
                for _ in range(10):  # Will try 4 times before skipping
                    successful = False  # Create a success flag
                    try:
                        details = self.extract_event_details(body_text, url)
                        event_details = [detail.replace('\n', '') for detail in
                                         details.split(';')]  # Removing newline characters
                        event_details.append(self.strip_url_parameters(url))

                        # Checking if the lengths of the extraction and the column mapping match
                        if len(event_details) - 1 != len(self.column_mapping):  # subtract 1 because we appended the URL
                            raise ValueError("Event details extraction failed. Retrying...")  # Raise an error to trigger the retry

                        event_details = self.parse_dates(event_details, datetime_fields)
                        event_details = self.parse_addresses(event_details, address_fields)

                        successful = True
                        break  # If successful, we break the loop and do not execute the 'else' clause.
                    except openai.error.OpenAIError:
                        print("OpenAI API error encountered. Retrying in 30 seconds...")
                        time.sleep(30)
                    except ValueError as e:
                        print(e)
                        continue
                    except PastDateError as e:
                        print(e)
                        break
                    except AddressParseError as e:
                        print(e)
                        continue
                    except Exception as e:
                        print(e)
                        continue

                if soup_flag == 'SHIFT':
                    if event_details:  # Check if the list is not empty
                        event_details[0] = 'BS to GPT: ' + event_details[0]
                    else:
                        event_details.append('BS to GPT: ')

                if not successful:
                    print("Failed to get the correct response from OpenAI. Marking error and moving to next URL.")
                    if event_details:  # Check if the list is not empty
                        event_details[0] = 'ERROR ' + event_details[0] # Replace the first value in the list with 'ERROR'
                    else:
                        event_details.append('ERROR ')  # If the list is empty, append 'ERROR'

            event_info.append(event_details)

        terms = ['Climate Change', 'Plants', 'Climate', 'Technology', 'Sustainability',
                 'Environmental Volunteering', 'Environment', 'Climate Tech',
                 'Renewable Energy', 'Emissions', 'Carbon', 'Agriculture', 'Biodiversity',
                 'Environmental Policy', 'Climate Awareness', 'Climate Advocacy',
                 'Reforestation', 'Recycling', 'Human Centric Design', 'Composting', 'Wildlife',
                 'Earth', 'Soil', 'Urban Modernization', 'Urban Restoration',
                 'Forestry', 'Ecosystems', 'Climate Investments', 'Climate Startups',
                 'Climate Legislation', 'Climate Activism', 'Recycled', 'Vintage', 'Compost'
                 'Vegan', 'Green', 'Sustainable Cities', 'Urbanism', 'Sustainable Nonprofits'
                 'Sustainable Buildings', 'Sustainable Design', 'Sustainable Architecture']

        event_info = [row + [value] for row, value in zip(event_info, self.check_relevance(event_info, terms))]
        self.write_events_to_csv(event_info, additional_data, self.output_file, self.column_mapping)
        pd.read_csv(self.output_file).pipe(lambda df: df.assign(Relevance=df.apply(lambda row: True if not pd.isna(row['Source CSV']) and 'eventbrite' not in row['Source CSV'].lower() else row['Relevance'], axis=1))).to_csv(self.output_file, index=False)

        print(f"The output CSV {self.output_file} has been saved. It contains {len(event_info)} rows.")
