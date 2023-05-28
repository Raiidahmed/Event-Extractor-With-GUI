# Event Data Web Scraper and Organizer

The Event Data Web Scraper and Organizer is a tool that allows you to extract event details from webpages, organize the extracted data, and store it in a CSV file. It is designed to simplify the process of collecting event information from multiple sources and make it easier to manage and analyze the data.

## Features

- Extracts event details from webpages using the OpenAI API.
- Supports reading URLs from CSV files.
- Customizable column mapping for organizing the extracted data.
- Allows specifying the number of rows to process for each CSV file.
- Provides options to select the output directory and file name for the generated CSV file.
- Ability to open the output file automatically upon completion.

## Prerequisites

Before using the Event Data Web Scraper and Organizer, ensure that you have the following:

- Python 3.6 or higher installed on your system.
- OpenAI API key. Sign up for an account on the OpenAI platform to obtain an API key.

## Installation

1. Clone the repository to your local machine:

git clone https://github.com/your-username/event-data-web-scraper.git

2. Navigate to the project directory:

cd event-data-web-scraper

3. Install the required dependencies using pip:

pip install -r requirements.txt

## Usage

### GUI Mode

The GUI mode provides a user-friendly interface for interacting with the Event Data Web Scraper and Organizer.

1. Run the following command to start the application:

python gui.py

2. The GUI window will open, allowing you to configure the extraction parameters:

- **Select URL Files**: Click the "Browse" button to select one or multiple CSV files containing the event URLs.
- **Select Output**: Click the "Browse" button to choose the output directory where the generated CSV file will be saved.
- **Rows to Process**: Enter the number of rows to process for each CSV file. Use "MAX" to scrape all rows.
- **API Key Env Var**: Enter your OpenAI API key environment variable.
- **Enter Identifier**: Provide an identifier such as the city name to specify the context of the events.
- **Column Mapping**: Specify the column mapping for organizing the extracted event data. Follow the provided format.

3. Click the "Run" button to start the extraction process. The extracted data will be saved in a CSV file in the specified output directory.

### Command-Line Mode

The command-line mode allows you to run the Event Data Web Scraper and Organizer without the GUI.

1. Open the `run.py` script in a text editor.

2. Modify the following variables based on your requirements:

- `csv_files`: Provide a list of CSV files containing the event URLs.
- `num_rows`: Specify the number of rows to process for each CSV file. Use "MAX" to scrape all rows.
- `city`: Provide an identifier such as the city name to specify the context of the events.
- `api_key_env`: Set your OpenAI API key environment variable.
- `Column_Mapping`: Customize the column mapping for organizing the extracted event data.
- `output_file_path`: Specify the output file path where the generated CSV file will be saved.

3. Save the changes and run the following command:

python run.py

4. The extraction process will start, and the extracted 