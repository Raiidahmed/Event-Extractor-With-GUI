import tkinter as tk
from tkinter import filedialog
from datasets import load_dataset, concatenate_datasets
from transformers import AutoTokenizer
from transformers import DataCollatorWithPadding
import evaluate
import numpy as np
from transformers import AutoModelForSequenceClassification, TrainingArguments, Trainer
from datetime import datetime
import logging
from transformers import set_seed

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy.compute(predictions=predictions, references=labels)

def load_csv_files():
    label2id = {False: 0, True: 1}

    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open file browser and allow user to select multiple files
    file_paths = filedialog.askopenfilenames(title="Select CSV files", filetypes=[("CSV files", "*.csv")])

    # Specify columns directly by their names
    data_columns = ['Event Name', 'Description', 'Organizer']
    label_column = 'Relevance'

    datasets = []
    for file_path in file_paths:
        dataset = load_dataset('csv', data_files=file_path)['train']

        # Logging the details about the loaded file
        logging.info(f"Loaded dataset from {file_path} with {len(dataset)} examples.")

        datasets.append(dataset)

    # Concatenate datasets
    concatenated_dataset = concatenate_datasets(datasets)

    if not hasattr(concatenated_dataset, 'map'):
        raise ValueError("Concatenated dataset is not a valid dataset object. Check the input datasets.")

    # Extract and concatenate data from specified columns
    concatenated_dataset = concatenated_dataset.map(
        lambda x: {'data': ' '.join([x[col] if x[col] is not None else '' for col in data_columns]),
                   'label': label2id[x[label_column]]})

    # Splitting into train, test, validation
    splits = concatenated_dataset.train_test_split(test_size=0.2)
    train_val = splits['train'].train_test_split(test_size=0.1)

    return train_val['train'], train_val['test'], splits['test']

def preprocess_function(examples):
    return tokenizer(examples["data"], truncation=True)

datetime = datetime.now().strftime('%Y%m%d_%H%M%S')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(f"Training Logs/training_log_{datetime}_.txt"),  # Log file location
        logging.StreamHandler()  # This will print logs to console as well
    ]
)

# Set a seed for reproducibility (optional but recommended)
set_seed(42)

path_to_existing_model = None # or "path/to/your/existing/model"

# Usage:
train_set, val_set, test_set = load_csv_files()

id2label = {0: "False", 1: "True"}
label2id = {"False": 0, "True": 1}

# Modify tokenizer and model loading based on whether we have an existing model or not
if path_to_existing_model:
    tokenizer = AutoTokenizer.from_pretrained(path_to_existing_model)
    model = AutoModelForSequenceClassification.from_pretrained(path_to_existing_model, num_labels=2, id2label=id2label, label2id=label2id)
else:
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2, id2label=id2label, label2id=label2id)


tokenized_train = train_set.map(preprocess_function, batched=True)
tokenized_test = val_set.map(preprocess_function, batched=True)
tokenized_val = test_set.map(preprocess_function, batched=True)

data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

accuracy = evaluate.load("accuracy")

# Update directory_name logic right before defining training_args
indicator = "_finetuned" if path_to_existing_model else ""
directory_name = f"/Users/raiidahmed/Desktop/Models/Model_{datetime}{indicator}"

training_args = TrainingArguments(
    output_dir=directory_name,
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=10,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    logging_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    logging_dir="Training Logs/logs",
    use_mps_device=True

)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

trainer.train()

# Evaluate on the test set after training
results = trainer.evaluate(tokenized_test)

# Print the results
print("Test Results:", results)



