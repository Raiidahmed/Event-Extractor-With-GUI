import tkinter as tk
from tkinter import messagebox
import psycopg2


def wipe_database():
    # Confirmation to ensure you really want to delete everything
    answer = messagebox.askyesno("Confirmation",
                                 "Are you sure you want to wipe the entire database? This action is irreversible.")

    if not answer:
        return

    # Connect to the PostgreSQL database
    '''conn = psycopg2.connect(
        dbname='CTC_Events_DB',
        user='Raiidahmed',
        password='Kidsoftheblackhole!3700',
        host='ctc-events.chdn12vvjsde.us-east-2.rds.amazonaws.com',
        port='5432'
    )'''

    conn = psycopg2.connect(
            dbname='ai_events_DB',
            user='Raiidahmed',
            password='Matanui123A!~',
            host='ai-events.chdn12vvjsde.us-east-2.rds.amazonaws.com',
            port='5432'
        )

    cursor = conn.cursor()

    cursor.execute("DELETE FROM events")
    conn.commit()
    print("Database wiped clean!")

    conn.close()


# Use a hidden tkinter root window for GUI operations
root = tk.Tk()
root.withdraw()

wipe_database()

# Close the hidden root window
root.destroy()
