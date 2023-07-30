import csv
import math
import openai
import os
import time

# Read the input CSV into a 2D array
data = []
openai.api_key = os.environ['OPENAI_API_KEY']
terms = ['Climate Change', 'Plants', 'Climate', 'Technology', 'Sustainability',
                 'Environmental Volunteering', 'Environment', 'Climate Tech',
                 'Renewable Energy', 'Emissions', 'Carbon', 'Agriculture', 'Biodiversity',
                 'Environmental Policy', 'Climate Awareness', 'Climate Advocacy',
                 'Reforestation', 'Recycling', 'Human Centric Design', 'Composting', 'Wildlife',
                 'Earth', 'Soil', 'Urban Modernization', 'Urban Restoration',
                 'Forestry', 'Ecosystems', 'Climate Investments', 'Climate Startups',
                 'Climate Legislation', 'Climate Activism', 'Recycled', 'Vintage', 'Compost'
                 'Vegan', 'Green', 'Sustainable Cities', 'Urbanism', 'Sustainable Nonprofits'
                 'Sustainable Buildings', 'Sustainable Design', 'Sustainable Architecture',
                 'Impact Investing', 'Local Produce', 'Farmers Market', 'Vegan Market', 'Vegetables',
                 'Plant Based']
def check_relevance(dataframe, terms, max_prompts_per_request=25):
    """
    Method to read input prompts from the dataframe and check their relevance against a list of terms using the GPT API.
    The method appends the relevance result to the dataframe.

    Parameters:
        terms (list[str]): List of terms against which relevance of the input strings is to be checked.
        max_prompts_per_request (int): Maximum number of input strings to be checked in a single API request.
    """
    term_string = ', '.join(terms)
    input_prompts = [row[0] for row in dataframe]
    num_prompts = len(input_prompts)
    num_requests = math.ceil(num_prompts / max_prompts_per_request)

    # Prepare a list to hold the relevance results
    relevance_results = []

    print("Starting the relevance check process...\n")

    for i in range(num_requests):
        retries = 0

        while retries < 10:
            try:
                start = i * max_prompts_per_request
                end = min((i + 1) * max_prompts_per_request, num_prompts)
                batch_prompts = input_prompts[start:end]

                # Prepare the prompt string with all batch prompts included
                batch_prompts_string = "\n---\n".join(batch_prompts)
                prompt_string = f"""
                For each of the following texts, give a single TRUE/FALSE value if it relates to even a single one of the following terms: {term_string}.
                THERE ARE {len(batch_prompts)} INPUTS, SO THERE SHOULD BE {len(batch_prompts)} OUTPUTS!
                The texts are:

                ---\n{batch_prompts_string}\n---"""

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a relevance checker. Use a semicolon character ; to delimit different fields extracted. Do not provide field names, just the extracted field.",
                        },
                        {"role": "user", "content": prompt_string},
                    ],
                )

                # Print out the model's response
                print(f"Response for batch {i + 1}:\n{response.choices[0]['message']['content']}\n")

                # Split the model's response by the semicolon character and remove leading/trailing whitespace
                batch_results = [res.strip() for res in response.choices[0]["message"]["content"].split(';')]

                if len(batch_results) != len(batch_prompts):
                    raise ValueError(
                        "Received a different number of results than expected. Please check the model's responses.")

                relevance_results.extend([result.lower() == 'true' for result in batch_results])

                print(f"Iteration {i + 1} of {num_requests} completed successfully.")
                break

            except Exception as e:
                retries += 1
                print(f"Error in iteration {i + 1}: {e}. Retry {retries} of 10.")
                time.sleep(2)  # Optional: sleep for 2 seconds before retrying
                if retries == 10:
                    print("Maximum retries exceeded. Breaking the loop.")
                    return

    # Append the results to the dataframe
    print("Relevance check process completed.")
    return (relevance_results)

with open('Output/Cleaned_CTC__events_2023_07_26_03_01_02.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        data.append(row)

for row in data:
    print(row)

data = [row + [value] for row, value in zip(data, check_relevance(data, terms))]

# Write the data into a new CSV file
with open('output1.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(data)
