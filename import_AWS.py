import csv
import tkinter as tk
from tkinter import filedialog
import psycopg2
from psycopg2 import sql
from psycopg2 import errors


def setup_database():
    # Connect to the PostgreSQL database and create the table
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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        event_name TEXT,
        start_date TIMESTAMP,
        end_date TIMESTAMP,
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

    # Read and insert data from the CSV
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

        # Check if the CSV matches the expected structure
        expected_header = ['Event Name', 'Start', 'End', 'Location', 'Description', 'Organizer', 'Event URL', 'City']
        if header != expected_header:
            raise ValueError("The provided CSV does not match the expected structure.")

        # Reporting: Starting import
        print("Starting the CSV import...")

        count = 0
        for row in reader:
            try:
                cursor.execute(
                    "INSERT INTO events (event_name, start_date, end_date, location, description, organizer, event_url, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    row)
                count += 1

                # Reporting: Print every 100 rows imported
                if count % 100 == 0:
                    print(f"Imported {count} rows so far...")
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                # Reporting: Duplicate URL
                print(f"Duplicate URL found for event: {row[0]}. Skipping...")
            else:
                conn.commit()

        # Reporting: Completion
        print(f"Import completed! {count} rows imported in total.")

    conn.close()

# Set up the database and table
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
