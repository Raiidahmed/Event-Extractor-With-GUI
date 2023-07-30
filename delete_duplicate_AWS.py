import csv
import tkinter as tk
from tkinter import filedialog
import psycopg2
from psycopg2 import errors

def delete_rows_from_db(csv_path):
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

    # Read data from the CSV
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

        expected_header = ['Event Name', 'Start', 'End', 'Location', 'Description', 'Organizer', 'Event URL', 'City']
        if header != expected_header:
            raise ValueError("The provided CSV does not match the expected structure.")

        print("Starting the CSV row deletion...")

        count = 0
        for row in reader:
            cursor.execute("DELETE FROM events WHERE event_url = %s", (row[6],))

            if cursor.rowcount > 0:  # Checks if any rows were affected (deleted)
                print(f"Found and deleted event: {row[0]} with URL: {row[6]}")
                count += 1
                conn.commit()

                if count % 100 == 0:
                    print(f"Deleted {count} rows so far...")

        print(f"Deletion completed! {count} rows deleted in total.")

    conn.close()


# Use a hidden tkinter root window to use the file dialog
root = tk.Tk()
root.withdraw()

# Immediately open the file browser to select a CSV
csv_path = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])

if not csv_path:
    print("No CSV file selected. Exiting...")
else:
    # If a file is selected, proceed with deleting rows in the database
    try:
        delete_rows_from_db(csv_path)
        print("Deletion process completed!")
    except ValueError as e:
        print(e)

# Close the hidden root window
root.destroy()
