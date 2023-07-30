import sqlite3
import csv
import tkinter as tk
from tkinter import filedialog

# Connect to the SQLite database
conn = sqlite3.connect('events.db')
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
                where_clauses.append("(start BETWEEN ? AND ?)")
                parameters.extend(value)
            elif column == "keyword":
                where_clauses.append("(event_name LIKE ? OR description LIKE ?)")
                keyword = f"%{value}%"  # Use SQL's LIKE for keyword search
                parameters.extend([keyword, keyword])
            else:
                where_clauses.append(f"{column} = ?")
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
    "city": "NYC",  # Export only events from 'nyc'.
    #"date_range": ("July 23, 2023", "July 30, 2023"),  # Events happening in September 2023
}

export_data_to_csv(filters)

conn.close()
