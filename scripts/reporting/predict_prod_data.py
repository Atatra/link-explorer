# Splits the prod_data.csv into sub csvs, based on the model attribute.

# load the csv prod_data.csv
import pandas as pd
import os

# Construct the absolute path to the CSV file
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, '../../data/prod_data.csv')

# Load the CSV file
df = pd.read_csv(csv_path)

# Split the data into sub dataframes based on the model attribute
sub_dfs = {}
for v in df['version'].unique():
    sub_dfs[v] = df[df['version'] == v]


# Save the sub dataframes to new CSV files

output_dir = os.path.join(base_dir, '../../data/reporting/split_prod_data')
os.makedirs(output_dir, exist_ok=True)

for k, v in sub_dfs.items():
    output_path = os.path.join(output_dir, f'prod_data_{k}.csv')
    v.to_csv(output_path, index=False)
