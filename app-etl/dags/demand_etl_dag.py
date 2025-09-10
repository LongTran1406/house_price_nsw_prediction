from pathlib import Path
import sys
from typing import Dict, Any
import os
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'common'))
sys.path.append(str(project_root / 'app-etl'))

os.chdir(project_root) # Change directory to read the files from ./data folder

from tasks.extract import ExtractTool
from tasks.transform import TransformTool
from tasks.load import LoadTool
from common.utils import read_config

class HousePriceETL:
    """
    A complete ETL Pipeline for handling the extract, transform and process steps
    Typical workflow:
    1. Extract (extract.py): Extract raw dataset from by scraping Realestate website
    2. Transform (transform.py): Transform dataset (preprocessing) and serve as Silver data
    3. Load (load.py): Load cleaned dataset to the datalake 
    """

    def __init__(self, config: Dict[str, Any]):
        """
        HousePriceETL class with a configuration dictionary for setting up ExtractTool, TransformTool, and LoadTool.
        
        Args:
            config: Dict[str, Any]: Configuration params for path and filename.
        Returns:
            None
        """
        self.config = config

        now = datetime.now()
        self.raw_folder = Path(self.config['data_manager']['raw_data_folder']) / f"year={now.year}" / f"month={now.strftime('%m')}" / f"day={now.strftime('%d')}"
        self.raw_file = self.raw_folder / f"{self.config['data_manager']['raw_database_name'].replace('.parquet','')}_{now.strftime('%Y%m%d')}.parquet"
        print(self.raw_file)

        self.checkpoint_file = self.raw_folder / "geocode_partial.csv"

        self.extract_tool = ExtractTool(self.config)
        self.transform_tool = TransformTool(self.config, self.raw_file, self.checkpoint_file)
        self.load_tool = LoadTool(self.config)

    def run(self):
        """
        Running the HousePriceETL by using ExtractTool, TransformTool, and LoadTool.
        
        Args:
            None
        Returns:
            None
        """
        df = self.extract_tool.extract()
        df = self.transform_tool.transform(df)
        self.load_tool.load(df)

if __name__ == '__main__':
    config_path = project_root / 'config' / 'config.yaml'
    config = read_config(config_path)
    etl = HousePriceETL(config)
    etl.run()


# etl = HousePriceETL()

# default_args = {
#     "owner": "airflow",
#     "retries": 2,
#     "retry_delay": timedelta(minutes=2)
# }

# with DAG(
#     dag_id="house_price_etl",
#     default_args=default_args,
#     description="House Pricing ETL pipeline with raw → processed → warehouse (OOP refactor)",
#     schedule_interval="@daily",
#     start_date=datetime(2025, 8, 1),
#     catchup=False,
#     tags=["house_price", "etl", "data-lake"]
# ) as dag:

#     extract_task = PythonOperator(
#         task_id="extract_raw",
#         python_callable=etl.extract
#     )

#     transform_task = PythonOperator(
#         task_id="transform",
#         python_callable=etl.transform
#     )

#     load_task = PythonOperator(
#         task_id="load",
#         python_callable=etl.load
#     )

#     extract_task >> transform_task >> load_task

