"""
Example script demonstrating how to use the RINEX 3 parser module.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from pygnsslab.io.rinex3.reader import Rinex3Reader
from pygnsslab.io.rinex3.writer import write_to_parquet
from pygnsslab.io.rinex3.utils import find_rinex3_files

def process_rinex_file(rinex_file, output_dir):
    """
    Process a RINEX 3 file, extracting metadata and observation data.
    
    Parameters:
    -----------
    rinex_file : str
        Path to the RINEX 3 file
    output_dir : str
        Path to the output directory
    
    Returns:
    --------
    tuple
        (metadata_file_path, parquet_file_path)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base filename without extension
    base_name = Path(rinex_file).stem
    
    # Create output file paths
    metadata_file = os.path.join(output_dir, f"{base_name}_metadata.json")
    parquet_file = os.path.join(output_dir, f"{base_name}_observations.parquet")
    
    # Read RINEX 3 file
    print(f"Reading RINEX file: {rinex_file}")
    rinex_reader = Rinex3Reader(rinex_file)
    
    # Get metadata and observations
    metadata = rinex_reader.metadata
    obs_data = rinex_reader.get_obs_data()
    
    # Save metadata to JSON
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_file}")
    
    # Save observations to parquet
    write_to_parquet(obs_data, parquet_file, metadata, metadata_file)
    print(f"Observations saved to: {parquet_file}")
    
    return metadata_file, parquet_file

def print_metadata_summary(metadata_file):
    """
    Print a summary of the metadata.
    
    Parameters:
    -----------
    metadata_file : str
        Path to the metadata JSON file
    """
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print("\nRINEX Metadata Summary:")
    print(f"  RINEX Version: {metadata.get('rinexVersion', 'N/A')}")
    print(f"  Station Name: {metadata.get('stationName', 'N/A')}")
    print(f"  Receiver Type: {metadata.get('receiverType', 'N/A')}")
    print(f"  Antenna Type: {metadata.get('antennaType', 'N/A')}")
    
    # Print observation types
    print("\nObservation Types:")
    for constellation, obs_types in metadata.get('observationTypes', {}).items():
        print(f"  {constellation}: {len(obs_types)} types")

def main():
    """
    Main function to demonstrate the RINEX 3 parser.
    """
    # Example file path (replace with an actual file path)
    rinex_file = os.path.join("data","obs","PTLD00AUS_R_20220010000_01D_30S_MO.rnx")
    
    # Check if the file exists
    if not os.path.exists(rinex_file):
        print(f"File not found: {rinex_file}")
        print("Please provide a valid RINEX 3 observation file path.")
        return
    
    # Process the file
    output_dir = "data/jsonpqt"
    metadata_file, parquet_file = process_rinex_file(rinex_file, output_dir)
    
    # Print metadata summary
    print_metadata_summary(metadata_file)
    
    # Alternatively, process all RINEX 3 files in a directory
    # rinex_dir = "rinex_data"
    # rinex_files = find_rinex3_files(rinex_dir)
    # for rinex_file in rinex_files:
    #     process_rinex_file(rinex_file, output_dir)

if __name__ == "__main__":
    main()