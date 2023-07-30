import os
import sys
import pickle
import subprocess
import threading
import traceback
from tkinter import filedialog, ttk
import tkinter as tk

from EventExtractor import EventExtractor


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.tooltip_id = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        self.tooltip_id = self.widget.after(500, self.create_tooltip)

    def hide_tooltip(self, event):
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None
            self.destroy_tooltip()

    def create_tooltip(self):
        if not self.tooltip_window:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
            y = self.widget.winfo_rooty() + self.widget.winfo_height() // 2

            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

            style = ttk.Style()
            style.configure("Tooltip.TLabel", background="white", padding=5, relief="solid", borderwidth=0,
                            bordercolor="gray", borderradius=5)

            label = ttk.Label(self.tooltip_window, text=self.text, style="Tooltip.TLabel")
            label.pack()

    def destroy_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class Console(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        sys.stdout = self

    def write(self, txt):
        self.config(state='normal')
        self.insert(tk.END, str(txt))
        self.see(tk.END)  # Scroll to the end
        self.config(state='disabled')

    def flush(self):
        pass


class App:
    def __init__(self, root):

        self.default_column_mapping = '''Event Name: The name of the event 
Start: The start datetime of the event in the following format: Month Day, Year, Hour:Minute AM/PM 
End: The end datetime of the event in the following format: Month Day, Year, Hour:Minute AM/PM 
Location: The full address of the event 
Description: A description of the event
Organizer: The organizer of the event'''

        self.open_file_var = tk.BooleanVar()
        self.root = root
        self.root.title("Event Extractor")
        window_width = 530
        window_height = 410
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

        # Add a threading.Event instance to your app
        self.stop_event = threading.Event()

        # Define Widgets
        width_std = 15

        self.button_cancel = tk.Button(root, text="Cancel", width=5, command=self.cancel_and_save)
        self.button_csv = tk.Button(root, text="Browse", command=self.load_csv_files)
        self.button_run = tk.Button(root, text="Run", width=5, command=self.run_event_extractor)
        self.button_output_dir = tk.Button(root, text="Browse", command=self.select_output_dir)

        script_dir = os.path.dirname(os.path.abspath(__file__))  # get directory of the script

        self.entry_api_key = tk.Text(root, width=width_std, height=1, highlightthickness=0)
        self.entry_city = tk.Text(root, width=width_std, height=1, highlightthickness=0)
        self.entry_num_rows = tk.Text(root, width=width_std, height=1, highlightthickness=0)
        self.entry_output_dir = tk.Text(root, width=width_std, height=1, highlightthickness=0)
        self.entry_output_dir.insert(tk.END, script_dir)  # default to directory of the script
        self.column_mapping_text = tk.Text(root, width=width_std, height=5, wrap=tk.NONE, highlightthickness=0)
        self.column_mapping_text.insert(tk.END, self.default_column_mapping)
        self.csv_display = tk.Text(root, height=3, width=width_std, highlightthickness=0)

        self.csv_display.config(state='disabled')
        self.entry_output_dir.config(state='disabled')

        self.label_api_key = tk.Label(root, text="API Key Env Var:")
        self.label_city = tk.Label(root, text="Enter Identifier:")
        self.label_column_mapping = tk.Label(root, text="Column Mapping:")
        self.label_csv = tk.Label(root, text="Select URL Files:")
        self.label_output = tk.Label(root, text="Select Output:")
        self.label_num_rows = tk.Label(root, text="Rows to Process:")
        self.checkbox_open_file = tk.Checkbutton(root, text="Open file upon completion", variable=self.open_file_var)

        # Add tooltips to buttons
        csv_tooltip = Tooltip(self.button_csv, "Shift click to select multiple csv files")
        output_dir_tooltip = Tooltip(self.button_output_dir, "Browse for the output directory")
        api_key_tooltip = Tooltip(self.entry_api_key, "Input API key environment variable")

        # Add tooltips to text widgets
        city_tooltip = Tooltip(self.entry_city, "The city name(s) are a good pick")
        column_mapping_tooltip = Tooltip(self.column_mapping_text, "Enter your output column:GPT prompt for data")
        num_rows_tooltip = Tooltip(self.entry_num_rows,
                                   "Enter the number of rows (separated by columns if you would\nlike to scrape different amounts of rows for multiple CSVs)\nand MAX if you want to scrape all rows")

        self.scrollbar_column_mapping = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.column_mapping_text.xview)
        self.open_file_var.set(False)

        # Grid Placement
        padx_std = 15
        pady_std = 10

        self.label_csv.grid(padx=padx_std, pady=pady_std, row=1, column=0, sticky="nw")
        self.csv_display.grid(pady=(pady_std, 5), row=1, column=1, sticky="w")

        self.button_csv.grid(row=2, pady=(0, pady_std), column=1, sticky="ew")

        self.entry_output_dir.grid(row=3, column=1, sticky="w")
        self.label_output.grid(padx=padx_std, row=3, column=0, sticky="w")

        self.button_output_dir.grid(row=4, pady=(0, pady_std), column=1, sticky="ew")

        self.label_num_rows.grid(padx=padx_std, pady=pady_std, row=5, column=0, sticky="w")
        self.entry_num_rows.grid(row=5, column=1, sticky="w")

        self.label_api_key.grid(padx=padx_std, row=6, column=0, sticky="w")
        self.entry_api_key.grid(row=6, column=1, sticky="w")

        self.label_city.grid(padx=padx_std, pady=pady_std, row=7, column=0, sticky="w")
        self.entry_city.grid(row=7, column=1, sticky="w")

        self.label_column_mapping.grid(padx=padx_std, pady=(0, pady_std), row=8, column=0, sticky="nw")
        self.column_mapping_text.grid(row=8, column=1, sticky='w')

        self.button_run.grid(row=9, column=0, pady=pady_std)
        self.button_cancel.grid(row=9, column=1)
        self.checkbox_open_file.grid(padx=12, row=9, column=2, columnspan=2)

        # Load saved data
        if os.path.exists('saved_data.pkl'):
            with open('saved_data.pkl', 'rb') as f:
                self.saved_data = pickle.load(f)

                self.csv_display.config(state='normal')
                self.entry_output_dir.config(state='normal')

                self.csv_display.delete('1.0', tk.END)
                self.csv_display.insert(tk.END, self.saved_data.get('csv', ''))

                self.entry_api_key.delete('1.0', tk.END)
                self.entry_api_key.insert(tk.END, self.saved_data.get('api_key', ''))

                self.entry_city.delete('1.0', tk.END)
                self.entry_city.insert(tk.END, self.saved_data.get('city', ''))

                self.entry_num_rows.delete('1.0', tk.END)
                self.entry_num_rows.insert(tk.END, self.saved_data.get('num_rows', ''))

                self.column_mapping_text.delete('1.0', tk.END)
                self.column_mapping_text.insert(tk.END,
                                                self.saved_data.get('column_mapping', self.default_column_mapping))

                self.entry_output_dir.delete('1.0', tk.END)
                self.entry_output_dir.insert(tk.END, self.saved_data.get('output_directory', ''))

                self.csv_display.config(state='disabled')
                self.entry_output_dir.config(state='disabled')

    def load_csv_files(self):
        self.csv_display.config(state='normal')
        initial_dir = os.path.dirname(self.csv_display.get("1.0", "end").strip()) if self.csv_display.get("1.0",
                                                                                                          "end").strip() else os.path.dirname(
            os.path.abspath(__file__))

        new_csv_files = list(filedialog.askopenfilenames(initialdir=initial_dir,
                                                         filetypes=(("CSV Files", "*.csv"), ("All files", "*.*"))))

        if new_csv_files:  # Check if the user selected any new files
            self.csv_files = new_csv_files  # Update the list of selected files

            self.csv_display.delete('1.0', tk.END)
            self.csv_display.insert(tk.END, ', '.join(self.csv_files))

        self.csv_display.config(state='disabled')

    def select_output_dir(self):
        self.entry_output_dir.config(state='normal')
        initial_dir = self.output_dir if hasattr(self, 'output_dir') else os.getcwd()

        new_output_dir = filedialog.askdirectory(initialdir=initial_dir, mustexist=True)

        # If the user selects a directory, update the output_dir and the text box
        if new_output_dir:
            self.output_dir = new_output_dir

            self.entry_output_dir.delete('1.0', tk.END)
            self.entry_output_dir.insert(tk.END, self.output_dir)

        self.entry_output_dir.config(state='disabled')

    def save_data(self):
        # Save data
        self.saved_data = {
            'csv': self.csv_display.get('1.0', 'end').strip(),
            'api_key': self.entry_api_key.get('1.0', 'end').strip(),
            'city': self.entry_city.get('1.0', 'end').strip(),
            'num_rows': self.entry_num_rows.get('1.0', 'end').strip(),
            'column_mapping': self.column_mapping_text.get('1.0', 'end').strip(),
            'output_directory': self.entry_output_dir.get('1.0', 'end').strip(),
        }
        with open('saved_data.pkl', 'wb') as f:
            pickle.dump(self.saved_data, f)

    def run_event_extractor(self):

        csv = self.csv_display.get('1.0', 'end').strip().split(', ') if len(self.csv_display.get('1.0', 'end')) > 1 else self.csv_display.get('1.0', 'end')
        api_key = self.entry_api_key.get('1.0', 'end').strip()
        num_rows = [x if x == 'MAX' else int(x) for x in self.entry_num_rows.get('1.0', 'end').strip().split(',')]
        city = self.entry_city.get('1.0', 'end')
        column_mapping_str = self.column_mapping_text.get('1.0', 'end')
        output_dir = self.entry_output_dir.get('1.0', 'end').strip()
        column_mapping = dict(item.split(": ", 1) for item in column_mapping_str.split("\n") if item)

        try:
            extractor = EventExtractor(api_key, csv, column_mapping, city, output_dir, num_rows)
            self.thread = threading.Thread(target=self.run_in_thread, args=(extractor,))
            self.thread.start()
        except Exception as e:
            traceback.print_exc()

    def run_in_thread(self, extractor):
        # This method will be called in a new thread
        try:
            extractor.run(self.stop_event)

            if self.open_file_var.get():
                # If the checkbox is checked, open the file here.
                # Replace the following line with the actual code to open your file.
                output_file_path = extractor.get_output_file()
                subprocess.call(["open", output_file_path])
        except:
            traceback.print_exc()

    def cancel_event_extractor(self):
        # Set the stop event
        self.stop_event.set()

    def cancel_and_save(self):
        self.cancel_event_extractor()
        self.save_data()
        self.root.quit()


root = tk.Tk()
root.resizable(False, False)
app = App(root)

frame = tk.Frame(root)
frame.place(x=265, y=10)

console = Console(frame, height=24, width=35, highlightthickness=0, state='disabled')
console.grid(row=0, column=0, )


def on_closing():
    app.cancel_event_extractor()
    app.save_data()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
