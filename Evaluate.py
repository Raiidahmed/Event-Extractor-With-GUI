import pandas as pd
from transformers import pipeline, DistilBertTokenizer, DistilBertForSequenceClassification
import tkinter as tk
from tkinter import filedialog
import torch

def create_prompt_from_row(row, indices):
    return ' '.join(str(row[i]) for i in indices)

def main():
    tokenizer = DistilBertTokenizer.from_pretrained("/Users/raiidahmed/Desktop/Models/Model_20230809_213204/checkpoint-480")
    model = DistilBertForSequenceClassification.from_pretrained("/Users/raiidahmed/Desktop/Models/Model_20230809_213204/checkpoint-480")

    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])

    if not file_path:
        print("No file selected. Exiting...")
        return

    df = pd.read_csv(file_path)
    indices = [0, 4, 5]
    truth = 7

    model.eval()

    true_labels = df["Relevance"].tolist()
    print(true_labels)
    predicted_labels = []

    for index, row in df.iterrows():
        prompt = create_prompt_from_row(row, indices)

        inputs = tokenizer(prompt, truncation=True, max_length=512, padding='max_length', return_tensors="pt")

        with torch.no_grad():
            logits = model(**inputs).logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            prediction = torch.argmax(probabilities, dim=1).item()

        sentiment = "True" if prediction == 1 else "False"
        confidence = probabilities[0][prediction].item()

        # Append predictions and confidence to the row
        df.at[index, 'Prediction'] = sentiment
        df.at[index, 'Confidence'] = confidence

        print(f"Row {index + 1} - Input: {prompt[:100]}... -> Sentiment: {sentiment}, Confidence: {confidence:.4f}")

        # For accuracy calculation
        predicted_labels.append(sentiment)

    # Save the updated DataFrame
    save_path = './Testing Results' + '/TESTED_' + file_path.split('/')[-1]
    df.to_csv(save_path, index=False)

    # Calculate accuracy
    correct_predictions = sum(1 for true, pred in zip(true_labels, predicted_labels) if str(true) == pred)
    accuracy = correct_predictions / len(true_labels)
    print(f"Accuracy rate: {accuracy:.4f}")


if __name__ == "__main__":
    main()
