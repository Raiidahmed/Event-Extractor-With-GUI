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

csv_files = ["CSV URL Data/amsterdam/climate_tech_eventbrite_climate_amsterdam.csv", "CSV URL Data/nyc/climate_tech_eventbrite_climate_nyc.csv"]
num_rows = [1, 1]  # Process all rows in the first CSV, and 10 rows in the second
city = "Amsterdam and nyc"
api_key_env = "OPENAI_API_KEY"

Column_Mapping = {
    'Event Name': 'The name of the event',
    'Description': 'a informative description of the event in 100 words or less',
    'Start': 'the start datetime of the event in the following format: Month Day, Year, Hour:Minute',
    'End': 'the end datetime of the event in the following format: Month Day, Year, Hour:Minute',
    'Location': 'The full address of the event',
    'City': 'the city the event takes place in',
    'Relevance': 'A single TRUE or FALSE value linked to whether the event is relevant to the following terms: Climate, Sustainability, Enviromental Volunteering, Environment, Climate Tech, Green, Clean, Renewable, Emissions, Carbon, Environmental Conservation, Climate Innovation, Agriculture, Transportation, Building, Energy, Waste, Water, Air, Biodiversity, Bioenergy, Geothermal, Hydroelectric, Solar, Wind, Efficiency, Environmental Policy, Climate Awareness, Climate Advocacy, Reforestation, Recycling, Composting, Ocean, Wildlife, Earth, Soil, Forestry, Ecosystems, Plastics, Climate Investments, Climate Startups, Climate Legislation, Climate Activism'
}

extractor = EventExtractor(api_key_env, csv_files, Column_Mapping, city, '/Users/raiidahmed/PycharmProjects/Event-Extractor-With-GUI', num_rows)
thread = threading.Thread(target=run_in_thread, args=(extractor, stop_event))
thread.start()
