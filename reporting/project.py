import os
import pandas as pd
from evidently.report import Report
from evidently.test_suite import TestSuite
from evidently.test_preset import DataQualityTestPreset, RegressionTestPreset
from evidently.metrics import (
    ColumnSummaryMetric, ColumnDistributionMetric, DatasetSummaryMetric,
    ColumnDriftMetric, DatasetDriftMetric
)
import datetime

print("Starting project.py...")  # Add this line to verify the script is running

# If ref_data_report does not exist, create it by predicting the target and adding the prediction column to the dataframe
# We need the prediction our first model makes on our reference data to compare it with the predictions made on the production data
# (It's not always going to be perfect, even on training data)
if os.path.exists("/data/reporting/evaluated_ref_data_sample.csv"): 
    ref_data = pd.read_csv("/data/reporting/evaluated_ref_data_sample.csv", delimiter=';')
else:
    # Error, you need to generate the prediction labels, needs to be done outside of this docker container
    raise ValueError("evaluated_ref_data_sample.csv does not exist. Please generate it by running refdata_evaluating_sampling.py")

# Print column names to verify
print("Reference data columns:", ref_data.columns)

# Add target and prediction columns if they do not exist
if 'target' not in ref_data.columns:
    ref_data['target'] = ref_data['rating']
if 'prediction' not in ref_data.columns:
    ref_data['prediction'] = ref_data['rating']  # Replace with actual predictions if available

datetime_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

BASE_PROJECT_NAME = "Link Predictor"
BASE_PROJECT_DESCRIPTION = datetime_stamp

# Function to create a report for a given model version
def create_report(version: str, ref_data, prod_data):
    # Print column names to verify
    print("Reference data columns:", ref_data.columns)
    print("Production data columns:", prod_data.columns)

    # Calculate derived metrics
    ref_data['summary_length'] = ref_data['abstract'].apply(len)
    ref_data['word_count'] = ref_data['abstract'].apply(lambda x: len(x.split()))
    prod_data['summary_length'] = prod_data['abstract'].apply(len)
    prod_data['word_count'] = prod_data['abstract'].apply(lambda x: len(x.split()))

    # Add target and prediction columns if they do not exist
    if 'target' not in prod_data.columns:
        prod_data['target'] = prod_data['rating']
    if 'prediction' not in prod_data.columns:
        prod_data['prediction'] = prod_data['rating']  # Replace with actual predictions if available

    report = Report(
        metrics=[
            DatasetSummaryMetric(),
            ColumnSummaryMetric(column_name="summary_length"),
            ColumnSummaryMetric(column_name="word_count"),
            ColumnSummaryMetric(column_name="rating"),
            ColumnDistributionMetric(column_name="rating"),
            ColumnDriftMetric(column_name="summary_length"),
            ColumnDriftMetric(column_name="word_count"),
            ColumnDriftMetric(column_name="rating"),
            DatasetDriftMetric(),
        ]
    )
    report.run(reference_data=ref_data, current_data=prod_data)
    return report

# Function to create test suites for a given model version
def create_test_suite(i: int, ref_data, prod_data):
    data_test_suite = TestSuite(
        tests=[
            DataQualityTestPreset(),
            RegressionTestPreset(),
        ],
        timestamp=datetime.datetime.now() + datetime.timedelta(days=i),
    )
    data_test_suite.run(reference_data=ref_data, current_data=prod_data)
    return data_test_suite

# Function to create projects and generate reports for each model version
def create_all_projects(workspace: str):
    # Ensure split_prod_data.py has been run to get all datasets separately for comparison
    current_versions = ["v1", "v2", "v3", "v4", "v5"]

    # Load reference data
    ref_data_path = os.path.join(workspace, 'reporting/evaluated_ref_data_sample.csv')
    print(f"Checking if reference data exists at: {ref_data_path}")
    if not os.path.exists(ref_data_path):
        raise ValueError("Evaluated reference data not found. Please generate it first using refdata_evaluating_sampling.py.")
    ref_data = pd.read_csv(ref_data_path, delimiter=';')

    # Add target and prediction columns if they do not exist
    if 'target' not in ref_data.columns:
        ref_data['target'] = ref_data['rating']
    if 'prediction' not in ref_data.columns:
        ref_data['prediction'] = ref_data['rating']  # Replace with actual predictions if available

    for version in current_versions:
        # Create a new project name for each model version
        project_name = f"{BASE_PROJECT_NAME}_{version}"
        project_description = f"{BASE_PROJECT_DESCRIPTION} - {version}"

        # Load production data for the current version
        prod_data_path = os.path.join(workspace, f'reporting/split_prod_data/prod_data_{version}.csv')
        print(f"Checking if production data exists at: {prod_data_path}")
        if not os.path.exists(prod_data_path):
            raise ValueError(f"Production data for version {version} not found.")
        prod_data = pd.read_csv(prod_data_path)

        # Add target and prediction columns if they do not exist
        if 'target' not in prod_data.columns:
            prod_data['target'] = prod_data['rating']
        if 'prediction' not in prod_data.columns:
            prod_data['prediction'] = prod_data['rating']  # Replace with actual predictions if available

        # Print column names to verify
        print(f"Production data columns for {version}:", prod_data.columns)

        # Create and run the report
        report = create_report(version, ref_data, prod_data)

        # Save the report
        artifact_folder = os.path.join(workspace, "artifacts/reports")
        os.makedirs(artifact_folder, exist_ok=True)
        report_name = f"{project_name}_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.html"
        report_path = os.path.join(artifact_folder, report_name)
        report.save_html(report_path)

        print(f"Report for {version} saved to {report_path}")

        # Create and run the test suite
        test_suite = create_test_suite(i=0, ref_data=ref_data, prod_data=prod_data)
        test_suite_path = os.path.join(artifact_folder, f"{project_name}_test_suite_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.html")
        test_suite.save_html(test_suite_path)

        print(f"Test suite for {version} saved to {test_suite_path}")

# Example usage
create_all_projects("/data")