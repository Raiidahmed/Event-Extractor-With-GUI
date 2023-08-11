import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime

# Create a root window and hide it
root = tk.Tk()
root.withdraw()

# Show an "Open File" dialog and allow multiple file selections
file_paths = filedialog.askopenfilenames(title="Select CSV files", filetypes=[("CSV files", "*.csv")])

if not file_paths:
    print("No files selected. Exiting...")
    exit()

print("Starting the CSV cleaning process...")
master_df = pd.DataFrame()

file_names = []
for file_path in file_paths:
    df = pd.read_csv(file_path)

    # Append the current DataFrame to master DataFrame
    master_df = master_df.append(df, ignore_index=True)

    # Collecting the filenames without extension
    file_names.append(os.path.splitext(os.path.basename(file_path))[0])

print("Removing rows that start with 'ERROR'...")
master_df[master_df.columns[0]] = master_df[master_df.columns[0]].fillna("").astype(str)
master_df = master_df[~master_df[master_df.columns[0]].str.startswith("ERROR")]

print("Removing empty columns...")
master_df = master_df.dropna(axis=1, how='all')

if 'Source CSV' in master_df.columns:
    print("Removing the 'Source CSV' column...")
    master_df = master_df.drop('Source CSV', axis=1)

print("Removing duplicate rows based on the 'Event Url' column...")
master_df = master_df.drop_duplicates(subset=['Event URL'], keep='first')

# Create target directory if it doesn't exist
if not os.path.exists("./Training Data"):
    os.makedirs("./Training Data")

# Save path with current date and time and input file names
current_date_time = datetime.now().strftime('%Y%m%d_%H%M%S')
joined_file_names = "_".join(file_names)
save_path = os.path.join("./Training Data", f"TRAIN_{joined_file_names}_{current_date_time}.csv")

master_df.to_csv(save_path, index=False)
print(f"File saved at: {save_path}")
