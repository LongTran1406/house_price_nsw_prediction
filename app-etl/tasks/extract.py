import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import json
from pathlib import Path
from datetime import datetime
# from airflow import DAG
# from airflow.operators.python import PythonOperator
from typing import Dict, Any
import os 
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'app-ml' / 'src'))
os.chdir(project_root) # Change directory to read the files from ./data folder

class ExtractTool:
    """
    An ExtractTool for scraping data from the real estate website, and save them in /data/raw
    """
    def __init__(self, config: Dict[str, Any]):
        """
        ExtractTool class with a configuration dictionary.
        
        Args:
            config: Dict[str, Any]: Configuration params for path and filename.
        Returns:
            None
        """
        self.config = config

    def extract(self):
        """
        Extracting steps:
        Get "address", "bedroom_nums", "bathroom_nums", "car_spaces", "land_size", "price" attributes from the website,
        Save raw file as .parquet format and .json for manifest file with date for better controlling
        Args:
            None
        Returns:
            None
        """
        records = []
        headers = ["address", "bedroom_nums", "bathroom_nums", "car_spaces", "land_size", "price"]
        records.append(headers)
        cnt = 0

        for step in range(0, 6):  # House size buckets
            driver = uc.Chrome()
            house_size_min = 200 + step * 200
            house_size_max = 200 + (step + 1) * 200
            print(f"Scraping size: {house_size_min}-{house_size_max} m²")

            for i in range(1, 80):  # Pages
                url = f"https://www.realestate.com.au/sold/property-house-size-{house_size_min}-{house_size_max}-in-nsw/list-{i}?maxSoldAge=1-month&source=refinement"
                driver.get(url)
                time.sleep(1)

                property_cards = driver.find_elements(By.CLASS_NAME, "residential-card__content")
                if not property_cards:
                    print(f"No more listings on page {i}, moving to next size bucket.")
                    break

                for card in property_cards:
                    cnt += 1
                    try:
                        address = card.find_element(By.CLASS_NAME, "residential-card__details-link").text.strip()
                    except:
                        address = None

                    bedroom_nums = bathroom_nums = car_spaces = land_size = price = None
                    features = card.find_elements(By.XPATH, ".//ul[contains(@class, 'residential-card__primary')]//li[@aria-label]")
                    for item in features:
                        label = item.get_attribute("aria-label").lower()
                        value = label.split(" ")[0]
                        if "bedroom" in label:
                            bedroom_nums = value
                        elif "bathroom" in label:
                            bathroom_nums = value
                        elif "car" in label:
                            car_spaces = value
                        elif "size" in label:
                            land_size = value

                    try:
                        price = card.find_element(By.CLASS_NAME, "property-price").text.strip()
                    except:
                        price = None

                    records.append([address, bedroom_nums, bathroom_nums, car_spaces, land_size, price])

                time.sleep(1)
                break
            driver.quit()
            break

        df = pd.DataFrame(records[1:], columns=records[0])

        # Save raw
        # now = datetime.now()
        # raw_folder = (
        #     Path(self.config['data_manager']['raw_data_folder'])
        #     / f"year={now.year}"
        #     / f"month={now.strftime('%m')}"
        #     / f"day={now.strftime('%d')}"
        # )
        # raw_folder.mkdir(parents=True, exist_ok=True)
        # raw_file = (
        #     raw_folder
        #     / f"{self.config['data_manager']['raw_database_name'].replace('.parquet','')}_{now.strftime('%Y%m%d')}.parquet"
        # )
        # df.to_parquet(raw_file, index = False)
        return df


        # manifest = {
        #     "file": str(raw_file),
        #     "rows": len(df),
        #     "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        # }

        # manifest_file = raw_folder / f"manifest_{now.strftime('%Y%m%d')}.json"

        # with open(manifest_file, "w") as f:
        #     json.dump(manifest, f, indent=2)

        # context['ti'].xcom_push(key="house_price_data", value=str(raw_file))

        # print(df.head())