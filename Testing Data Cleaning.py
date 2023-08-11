import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os

# Create a root window and hide it
root = tk.Tk()
root.withdraw()

# Show an "Open File" dialog
file_path = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])

if not file_path:
    print("No file selected. Exiting...")
    exit()

print("Starting the CSV cleaning process...")
df = pd.read_csv(file_path)

print("Removing rows that start with 'ERROR'...")
df[df.columns[0]] = df[df.columns[0]].fillna("").astype(str)
df = df[~df[df.columns[0]].str.startswith("ERROR")]

print("Removing empty columns...")
df = df.dropna(axis=1, how='all')

if 'Source CSV' in df.columns:
    print("Removing the 'Source CSV' column...")
    df = df.drop('Source CSV', axis=1)

# Create target directory if it doesn't exist
if not os.path.exists("./Testing Data"):
    os.makedirs("./Testing Data")

# Extract filename and set the save path
filename = os.path.basename(file_path)
save_path = os.path.join("./Testing Data/TEST_" + filename)

df.to_csv(save_path, index=False)
print(f"File saved at: {save_path}")
