import openai
import pandas as pd
import os

# DO NOT RUN, WITHOUT FUNCTIONING OPENAI API (not in repo) KEY MIGHT ERASE EVALUATED DATA SAMPLE

# Construct the absolute path to the CSV file
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, '../../data/ref_data.csv')

# Load the CSV file
df = pd.read_csv(csv_path)

# Sample 10 random lines to reduce API usage
sampled_df = df.sample(n=30)

# Construct the absolute path to the API key file
api_key_path = os.path.join(base_dir, 'openai-api-key.txt')

# Load openai API key from non versioned file
with open(api_key_path, 'r') as file:
    openai.api_key = file.read().replace('\n', '')

# Function to evaluate abstract quality
def evaluate_abstract(article, abstract):
    prompt = f"Evaluate the quality of the following abstract on grading from 1 to 5 based on the article:\n\nArticle: {article}\n\nAbstract: {abstract}\n\nCriteria: Relevance, coherence, completeness, and conciseness."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

# Apply the evaluation function to each row in the sampled dataframe
sampled_df['rating'] = sampled_df.apply(lambda row: evaluate_abstract(row['article'], row['abstract']), axis=1)

# Save the results to a new CSV file
output_path = os.path.join(base_dir, '../../data/reporting/evaluated_ref_data_sample.csv')
sampled_df.to_csv(output_path, index=False)