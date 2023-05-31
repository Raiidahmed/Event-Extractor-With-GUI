from EventExtractor import EventExtractor
import threading
import traceback

def run_in_thread(extractor, stop_event):
    try:
        extractor.run(stop_event)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()  # print the full traceback

# Initialize threading.Event
stop_event = threading.Event()

csv_files = ["climate_tech_eventbrite_climate_amsterdam.csv", "climate_tech_eventbrite_climate_nyc.csv"]
num_rows = [1, 1]  # Process all rows in the first CSV, and 10 rows in the second
city = "Amsterdam and nyc"
api_key_env = "OPENAI_API_KEY"

Column_Mapping = {
    'Event Name': 'The name of the event',
    'Short Description': 'a short but informative description of the event',
    'Start': 'the start datetime of the event in the following format: YYYY-MM-DD HH:MM',
    'End': 'the end datetime of the event in the following format: YYYY-MM-DD HH:MM',
    'Location': 'The full address of the event',
    'City': 'the city the event takes place in',
    'Relevance': 'A TRUE or FALSE value linked to whether the event is relevant to climate tech or not'
}

extractor = EventExtractor(api_key_env, csv_files, Column_Mapping, city, 'output.csv', num_rows)
thread = threading.Thread(target=run_in_thread, args=(extractor, stop_event))
thread.start()
