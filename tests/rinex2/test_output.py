import json
import pandas as pd
from pathlib import Path

def test_read_rinex2_files():
    # Define the base directory and file paths
    base_dir = Path(__file__).parent.parent.parent
    json_file = base_dir / "data" / "jsonpqt" / "ajac0010_metadata.json"
    parquet_file = base_dir / "data" / "jsonpqt" / "ajac0010_observations.parquet"

    # Read and print JSON metadata
    print("\n=== Reading JSON Metadata ===")
    with open(json_file, 'r') as f:
        metadata = json.load(f)
    print(json.dumps(metadata, indent=2))

    # Read and print Parquet observations
    print("\n=== Reading Parquet Observations ===")
    df = pd.read_parquet(parquet_file)
    print("\nDataFrame Info:")
    print(df.info())
    print("\nFirst few rows of the DataFrame:")
    print(df)

if __name__ == "__main__":
    test_read_rinex2_files()
