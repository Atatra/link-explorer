import datetime
import os
import pickle

import pandas as pd

from evidently.report import Report
from evidently.ui.workspace import Workspace, WorkspaceBase

from evidently.ui.dashboards import CounterAgg, DashboardPanelCounter, DashboardPanelPlot, PanelValue, PlotType, ReportFilter

from evidently.metrics import ColumnDistributionMetric, DatasetCorrelationsMetric, ColumnSummaryMetric, DatasetSummaryMetric, ClassificationQualityMetric, ClassificationClassBalance, ClassificationConfusionMatrix
from evidently.metrics import DatasetDriftMetric, ColumnDriftMetric

from evidently.test_preset import BinaryClassificationTestPreset, DataQualityTestPreset
from evidently.test_suite import TestSuite
from evidently.tests import *




# If ref_data_report does not exist, create it by predicting the target and adding the prediction column to the dataframe
# We need the prediction our first model makes on our reference data to compare it with the predictions made on the production data
# (It's not always going to be perfect, even on training data)
if os.path.exists("/data/evaluated_ref_data_sample.csv"): 
    ref_data = pd.read_csv("/data/evaluated_ref_data_sample.csv")
else:
    # Error, you need to generate the prediction labels, needs to be done outside of this docker container
    raise ValueError("evaluated_ref_data_sample.csv does not exist. Please generate it by running refdata_evaluating_sampling.py")

# Load prod_data.csv

# Do we want to split by model (prod_data model attribute ? if so how can we allow the user to choose which model to compare to
# baseline model ?)



# prod_data = pd.read_csv("/data/prod_data.csv")

WORKSPACE = "workspace"

date_time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%Ss")

BASE_PROJECT_NAME = "Link Explorer"
BASE_PROJECT_DESCRIPTION = date_time_stamp
# TODO ADD DIFFERENT NAMES FOR THE DIFFERENT MODELS (IN THE CREATE)


def create_report(i: int, ref_data, prod_data):
    data_report = Report(
        metrics=[
            DatasetSummaryMetric(),
            ColumnSummaryMetric(column_name="target"),
            ColumnSummaryMetric(column_name="prediction"),
            ClassificationClassBalance(),
            ColumnDistributionMetric(column_name="target"),
            ColumnDistributionMetric(column_name="prediction"),
            ClassificationQualityMetric(),
            DatasetCorrelationsMetric(),
            ClassificationConfusionMatrix(),
            DatasetDriftMetric(),  # Add dataset drift metric
            ColumnDriftMetric(column_name="target"),  # Add column drift metric for target
            ColumnDriftMetric(column_name="prediction"),  # Add column drift metric for prediction
        ],
        timestamp=datetime.datetime.now() + datetime.timedelta(days=i),
    )

    data_report.run(reference_data=ref_data, current_data=prod_data)
    return data_report


def create_test_suite(i: int):
    data_test_suite = TestSuite(
        tests=[
            DataQualityTestPreset(),
            BinaryClassificationTestPreset(),

        ],
        timestamp=datetime.datetime.now() + datetime.timedelta(days=i),
    )

    data_test_suite.run(reference_data=ref_data, current_data=prod_data)
    return data_test_suite


def create_project(workspace: WorkspaceBase):
    project = workspace.create_project(YOUR_PROJECT_NAME)
    project.description = YOUR_PROJECT_DESCRIPTION

    project.dashboard.add_panel(
        DashboardPanelCounter(
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            agg=CounterAgg.NONE,
            title="RAVDESS DATASET",
        )
    )

    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Nombre de données dans Prod data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="DatasetSummaryMetric",
                field_path=DatasetSummaryMetric.fields.current.number_of_rows,
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Nombre de données dans Ref Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="DatasetSummaryMetric",
                field_path=DatasetSummaryMetric.fields.reference.number_of_rows,
                legend="Ref Data",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )

    project.dashboard.add_panel(
        DashboardPanelCounter(
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            agg=CounterAgg.NONE,
            title="Scores",
        )
    )

    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Accuracy Prod Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.current.accuracy,
                legend="Accuracy",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Accuracy Ref Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.reference.accuracy,
                legend="Accuracy",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )

    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Precision Prod Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.current.precision,
                legend="Precision",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Precision Ref Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.reference.precision,
                legend="Precision",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Recall Prod Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.current.recall,
                legend="Recall",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Recall Ref Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.reference.recall,
                legend="Recall",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="F1 Prod Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.current.f1,
                legend="F1",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="F1 Ref Data",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="ClassificationQualityMetric",
                field_path=ClassificationQualityMetric.fields.reference.f1,
                legend="F1",
            ),
            text="",
            agg=CounterAgg.LAST,
            size=1,
        )
    )

    project.dashboard.add_panel(
        DashboardPanelPlot(
            title="Target Column Drift",
            filter=ReportFilter(
                metrics=[ColumnDriftMetric(column_name="target")],
                metadata_values=[],
                tag_values=[]
            ),
            plot_type=PlotType.BAR,
            values=[PanelValue(
                metric_id="ColumnDriftMetric",
                field_path="drift_score",
                legend="Target Drift",
            )],
        )
    )

    project.dashboard.add_panel(
        DashboardPanelPlot(
            title="Prediction Column Drift",
            filter=ReportFilter(
                metrics=[ColumnDriftMetric(column_name="prediction")],
                metadata_values=[],
                tag_values=[]
            ),
            plot_type=PlotType.BAR,
            values=[PanelValue(
                metric_id="ColumnDriftMetric",
                field_path="drift_score",
                legend="Prediction Drift",
            )],
        )
    )

    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Share of Drifted Features",
            value=PanelValue(
                metric_id="DatasetDriftMetric",
                field_path="drift_share",
                legend="Drifted Features",
            ),
            filter=ReportFilter(
                metrics=[DatasetDriftMetric],
                metadata_values=[],
                tag_values=[]
            ),
            agg=CounterAgg.SUM,
        )
    )

    project.save()
    return project


def save_report_to_file(report, report_path):
    with open(report_path, 'wb') as file:
        pickle.dump(report, file)


def load_report_from_file(report_path):
    with open(report_path, 'rb') as file:
        report = pickle.load(file)
    return report


def add_existing_reports_to_project(ws, project, artifact_path):
    # Liste des fichiers dans le dossier artifacts
    artifact_report_files = [f for f in os.listdir(artifact_path) if f.startswith("report_")]

    for report_file in artifact_report_files:
        report_path = os.path.join(artifact_path, report_file)

        try:
            # Utiliser la fonction pour charger un rapport à partir du fichier
            opened_artifact_report = load_report_from_file(report_path)

            # Ajouter le rapport au projet
            ws.add_report(project.id, opened_artifact_report)
        except Exception as e:
            print(f"Erreur lors du chargement du rapport {report_file}: {e}")


def create_all_projects(workspace: str):
    # Ensure split_prod_data.py has been run to get all datasets separately for comparison
    current_versions = ["v1", "v2", "v3", "v4", "v5"]

    print("Checking if production data has been updated...")
    raise ValueError("Check to see if file updates")
    # Load reference data
    ref_data_path = os.path.join(workspace, '/data/reporting/evaluated_ref_data_sample.csv')
    if not os.path.exists(ref_data_path):
        raise ValueError("Evaluated reference data not found. Please generate it first using refdata_evaluating_sampling.py.")
    ref_data = pd.read_csv(ref_data_path)

    for version in current_versions:
        # Create a new project name for each model version
        project_name = f"{BASE_PROJECT_NAME}_{version}"
        project_description = f"{BASE_PROJECT_DESCRIPTION} - {version}"

        # Load production data for the current version
        prod_data_path = os.path.join(workspace, f'data/reporting/split_prod_data/prod_data_{version}.csv')
        if not os.path.exists(prod_data_path):
            raise ValueError(f"Production data for version {version} not found.")
        prod_data = pd.read_csv(prod_data_path)

        # Create and run the report
        report = create_report(version, ref_data, prod_data)

        # Save the report
        artifact_folder = os.path.join(workspace, "artifacts/reports")
        os.makedirs(artifact_folder, exist_ok=True)
        report_name = f"{project_name}_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.html"
        report_path = os.path.join(artifact_folder, report_name)
        report.save_html(report_path)

        print(f"Report for {version} saved to {report_path}")

if __name__ == "__main__":
    create_all_project(WORKSPACE)
