Event Extractor

Event Extractor is a powerful Python-based script and application designed to extract and filter event data from a set of given CSV files. The application utilizes the OpenAI API for information extraction and processes the data on a separate thread for efficiency. The script reads in URLs from CSV files, visits each URL, scrapes its content, and uses the OpenAI API to extract specified event details from the content. The extracted information is then written to an output CSV file.

Features

Extract and filter event data from provided CSV files.
Process the data on a separate thread for efficient execution.
Utilize OpenAI API for information extraction.
Custom column mapping to provide descriptive labels for your data.
Flexible event relevance filtering based on the 'Relevance' column in your data.
GUI Application built with Tkinter allowing for dynamic configuration of process parameters.
Ability to save and load user settings on the GUI application.
Option to open the output file upon completion of data extraction.
Provision to stop the processing at any time.
Dependencies

This script and application require Python 3.6+ and the following Python libraries installed:

os
sys
pickle
subprocess
threading
traceback
tkinter
ttk
pandas
requests
openai
BeautifulSoup from bs4
Before running the script, make sure to install these dependencies. This can be done via pip:

```
pip install -r requirements.txt
```

The script also requires an OpenAI API key.

Installation

Clone this repository to your local machine.

```
git clone https://github.com/username/EventExtractor.git
```

Install the required packages.

```
pip install -r requirements.txt
```

Usage

Before running the script, please ensure you have correctly set up your OpenAI API key in your environment variables:

```
export OPENAI_API_KEY='your-api-key'
```

You can then run the script as follows:

```
python script.py
```

Or use it as a class named EventExtractor in your Python code:

from threading import Event

```
stop_event = Event()
event_extractor = EventExtractor("OPENAI_API_KEY", ["urls.csv"], {"event": "Event Name", "date": "Event Date"}, "San Francisco", num_rows=100)
event_extractor.run(stop_event)
```

For the GUI Application:

Run the script, this will launch the GUI.
Click the "Browse" button next to "Select URL Files" and select the CSV file(s) you want to process.
Specify the output directory by clicking "Browse" button next to "Select Output".
Enter the number of rows you want to process from each CSV file.
Input the API Key for the EventExtractor.
Specify the Identifier.
Map the columns in your CSV file to the attributes of the event. This can be done in the "Column Mapping" textbox.
Click "Run" to start processing the CSV files.
You can stop the processing at any time by clicking "Cancel".
The processing log will be displayed in the console on the GUI.
If you want to open the output file upon completion, check the box "Open file upon completion".
If you close the application, your settings will be saved and loaded the next time you open it.
Configuration

The following is a description of the main configuration elements within the script:

csv_files: A list of CSV files you want to extract event data from.
num_rows: A list of integers indicating how many rows you want to process in each corresponding CSV file. Each integer corresponds to a CSV file in the 'csv_files' list.
city: A string representing the city or cities you are interested in for the events.
api_key_env: The name of the environment variable where your OpenAI API key is stored.
Column_Mapping: A dictionary object where the keys represent the column headers in your CSV file, and the values represent the descriptive labels for these columns.
'output.csv': The output file where the filtered data will be written to.
Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Please make sure to update tests as appropriate.
