import sqlite3
import csv
import tkinter as tk
from tkinter import filedialog


def setup_database():
    # Connect to the SQLite database and create the table
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT,
        start TEXT,
        end TEXT,
        location TEXT,
        description TEXT,
        organizer TEXT,
        event_url TEXT UNIQUE,
        city TEXT
    )
    ''')
    conn.commit()
    conn.close()


def import_csv_to_db(csv_path):
    # Connect to the SQLite database
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Read and insert data from the CSV
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

        # Check if the CSV matches the expected structure
        expected_header = ['Event Name', 'Start', 'End', 'Location', 'Description', 'Organizer', 'Event URL', 'City']
        if header != expected_header:
            raise ValueError("The provided CSV does not match the expected structure.")

        for row in reader:
            try:
                cursor.execute(
                    "INSERT INTO events (event_name, start, end, location, description, organizer, event_url, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    row)
            except sqlite3.IntegrityError:
                print(f"Duplicate URL found for event: {row[0]}. Skipping...")

    conn.commit()
    conn.close()


# Setup the database and table
setup_database()

# Use a hidden tkinter root window to use the file dialog
root = tk.Tk()
root.withdraw()

# Immediately open the file browser to select a CSV
csv_path = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])

if not csv_path:
    print("No CSV file selected. Exiting...")
else:
    # If a file is selected, import it to the database
    try:
        import_csv_to_db(csv_path)
        print("CSV imported successfully!")
    except ValueError as e:
        print(e)

# Close the hidden root window
root.destroy()
