import csv
import tkinter as tk
from tkinter import filedialog
import psycopg2

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

cursor = conn.cursor()

def export_data_to_csv(filters=None):
    # Build the query and parameters
    query = "SELECT * FROM events"
    parameters = []

    # If filters provided, construct WHERE clause
    if filters:
        where_clauses = []
        for column, value in filters.items():
            if column == "date_range":
                # Assuming date_range provides a tuple (start_date, end_date)
                where_clauses.append("(start_date BETWEEN %s AND %s)")
                parameters.extend(value)
            elif column == "keyword":
                where_clauses.append("(event_name LIKE %s OR description LIKE %s)")
                keyword = f"%{value}%"
                parameters.extend([keyword, keyword])
            else:
                where_clauses.append(f"{column} = %s")
                parameters.append(value)
        query += " WHERE " + " AND ".join(where_clauses)

    cursor.execute(query, parameters)

    # Fetch data
    data = cursor.fetchall()

    # Get path to save the CSV
    csv_path = filedialog.asksaveasfilename(title="Save as CSV", filetypes=[("CSV files", "*.csv")], defaultextension=".csv")

    if not csv_path:
        return

    # Write data to CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Event Name', 'Start', 'End', 'Location', 'Description', 'Organizer', 'Event URL', 'City'])
        writer.writerows(data)

# Filters can be set here by the user

# Filters can be set here by the user
'''"england--london": "London",
   "ca--los-angeles": "LA",
   "dc--washington": "DC",
   "il--chicago": "Chicago",
   "netherlands--amsterdam": "Amsterdam",
   "ny--new-york": "NYC",
   "singapore--singapore": "Singapore",
   "ca--san-francisco": "SF",
   "wa--seattle": "Seattle",
   "ma--boston": "Boston",
   "canada--montreal": "MTL"'''

filters = {
    "city": "NYC",  # Export only events from 'NYC'.
    "date_range": ("2023-07-30", "2023-08-20"),
}

export_data_to_csv(filters)

conn.close()
