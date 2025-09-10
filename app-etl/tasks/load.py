import os
from pathlib import Path
from datetime import datetime
import sys
from typing import Dict, Any
import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'app-ml' / 'src'))
sys.path.append(str(project_root / 'app-etl'))
os.chdir(project_root) # Change directory to read the files from ./data folder

class LoadTool:
    """
    A LoadTool for saving the enriched dataset to cleaned folder
    """
    def __init__(self, config: Dict[str, Any]):
        """
        LoadTool class with a configuration dictionary.
        
        Args:
            config: Dict[str, Any]: Configuration params for path and filename.
        Returns:
            None
        """
        self.config = config
    
    def load(self, df: pd.DataFrame):
        """
        Function to load enriched dataset to cleaned folder

        Args:
            pd.DataFrame: Input data frame for saving
        Returns:
            None
        """
        # now = datetime.now()
        # raw_folder = Path(self.config['data_manager']['prod_data_folder'])
        # raw_folder.mkdir(parents=True, exist_ok=True)
        # raw_file = raw_folder / self.config['data_manager']['prod_database_name']


        now = datetime.now()
        raw_folder = (
            Path(self.config['data_manager']['raw_data_folder'])
            / f"year={now.year}"
            / f"month={now.strftime('%m')}"
            / f"day={now.strftime('%d')}"
        )
        raw_folder.mkdir(parents=True, exist_ok=True)
        raw_file = (
            raw_folder
            / f"{self.config['data_manager']['raw_database_name'].replace('.parquet','')}_{now.strftime('%Y%m%d')}.parquet"
        )
        df.to_parquet(raw_file, index = False)


