import os
import pandas as pd

# Construct the absolute path to the CSV file
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, '../../data/ref_data.csv')

# Load the CSV file
df = pd.read_csv(csv_path)

# Sample 30 random lines (tried a 100, it's really too much)
sampled_df = df.sample(n=30)

# Write the sampled lines to a new CSV file
output_path = os.path.join(base_dir, '../../data/reporting/ref_data_sample.csv')
sampled_df.to_csv(output_path, index=False)