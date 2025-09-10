import pandas as pd
import re
import os
import requests
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
load_dotenv()
from pathlib import Path
import time
from datetime import datetime
import sys
from typing import Dict, Any

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'app-ml' / 'src'))
os.chdir(project_root) # Change directory to read the files from ./data folder


class TransformTool:
    """
    An TransformTool for enriching the collected raw dataset with more features such as latitude, longtitude, postcode, etc...
    """
    def __init__(self, config: Dict[str, Any], raw_file, checkpoint_file):
        """
        TransformTool class with a configuration dictionary.
        
        Args:
            config: Dict[str, Any]: Configuration params for path and filename.
        Returns:
            None
        """
        self.config = config
        self.raw_file = raw_file
        self.checkpoint_file = checkpoint_file
        # now = datetime.now()
        # self.raw_folder = Path(self.config['data_manager']['raw_data_folder']) / f"year={now.year}" / f"month={now.strftime('%m')}" / f"day={now.strftime('%d')}"
        # self.raw_file = self.raw_folder / f"{self.config['data_manager']['raw_database_name'].replace('.parquet','')}_{now.strftime('%Y%m%d')}.parquet"
        # print(self.raw_file)
        # self.checkpoint_file = self.raw_folder / "geocode_partial.csv"
        
    def transform(self, df) -> pd.DataFrame:
        """
        transform step for interacting with API to gather data.
        
        Args:
            None
        Returns:
            pd.DataFrame: Output enriched dataset
        """
        # ti = context['ti']
        # raw_records = ti.xcom_pull(task_ids="extract_raw", key="house_price_data")
        # df = pd.DataFrame(raw_records)
        
        # ti.xcom_push(key="processed_data", value=df.to_dict(orient="records"))

        # Load environment variables
        
        key1 = os.getenv("LOCATIONIQ_KEY_1")
        key2 = os.getenv("LOCATIONIQ_KEY_2")
        key3 = os.getenv("LOCATIONIQ_KEY_3")

        # Load data
        # df = pd.read_parquet(self.raw_file)

        # Geocoding setup
        api_keys = [
            key1, 
            key2, 
            key3
        ]
        url = "https://us1.locationiq.com/v1/search"

        # Load checkpoint if exists
        # if not os.path.exists(self.checkpoint_file):
# Ensure parent folder exists
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)

        # Create empty checkpoint file with headers
        pd.DataFrame(columns=['index','lat','lon','postcode','city']).to_csv(
            self.checkpoint_file, index=False
        )


        # Load checkpoint if exists
        df_geo = pd.read_csv(self.checkpoint_file)
        done_indices = set(df_geo['index']) if not df_geo.empty else set()


        total = len(df)

        # Split indices into 3 roughly equal parts, one per API key
        indices_chunks = []
        chunk_size = (total + 2) // 3  # ceiling division

        for i in range(3):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total)
            indices_chunks.append(list(range(start_idx, end_idx)))
        
            
        def geocode_worker(indices, api_key):
            global processed_count
            processed_count = 0
            results = []
            for i in indices:
                if i in done_indices:
                    processed_count += 1
                    print(f"Skipping {i}/{total} (already done). Progress: {processed_count}/{total}")
                    continue

                params = {
                    'key': api_key,
                    'q': df['address'].iloc[i],
                    'format': 'json'
                }

                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    if isinstance(data, list) and len(data) > 0:
                        lat = float(data[0]['lat'])
                        lon = float(data[0]['lon'])
                        match = re.search(r'\b\d{4}\b', data[0]['display_name'])
                        postcode = int(match.group()) if match else None
                        display_parts = [part.strip() for part in data[0]['display_name'].split(',')]
                        print(display_parts)
                        if 'Sydney' in display_parts:
                            city = 'Sydney'
                        elif 'Newcastle' in display_parts:
                            city = 'Newcastle'
                        elif 'Wollongong' in display_parts:
                            city = 'Wollongong'
                        else:
                            city = None
                    else:
                        lat, lon, postcode, city = None, None, None, None
                except Exception as e:
                    print(f"Error on row {i}: {e}")
                    lat, lon, postcode, city = None, None, None, None

                processed_count += 1
                print(f"Processed {i}/{total}. Progress: {processed_count}/{total}")

                # Append result immediately to checkpoint file
                pd.DataFrame([[i, lat, lon, postcode, city]], columns=['index', 'lat', 'lon', 'postcode', 'city']).to_csv(
                    self.checkpoint_file, mode='a', index=False, header=not os.path.exists(self.checkpoint_file)
                )

                # Be polite to API
                time.sleep(0.7)
            return True


        # Run 3 workers concurrently, each with its own API key
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for idx_chunk, api_key in zip(indices_chunks, api_keys):
                futures.append(executor.submit(geocode_worker, idx_chunk, api_key))
            for future in as_completed(futures):
                future.result()  # wait for completion

        df_geo = pd.read_csv(self.checkpoint_file)
        df_geo = df_geo.sort_values('index').reset_index(drop=True)
        df = df.join(df_geo[['lat','lon','postcode','city']])
        df = df[(df['lat'] <= 0) & (df['lon'] >= 0)]
        print(df.head())
        return df
