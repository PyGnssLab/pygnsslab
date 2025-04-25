"""
Example script demonstrating how to use the RINEX 2 parser module.
"""

import os
import json
from pathlib import Path
from pygnsslab.rinex2.reader import Rinex2Reader
from pygnsslab.rinex2.writer import write_to_parquet
from pygnsslab.rinex2.utils import find_rinex2_files

def process_rinex_file(rinex_file, output_dir):
    """
    Process a RINEX 2 file, extracting metadata and observation data.
    
    Parameters:
    -----------
    rinex_file : str
        Path to the RINEX 2 file
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
    
    # Read RINEX 2 file
    print(f"Reading RINEX file: {rinex_file}")
    rinex_reader = Rinex2Reader(rinex_file)
    
    # Get metadata and observations
    metadata = rinex_reader.metadata
    obs_data = rinex_reader.get_obs_data()
    
    # Convert datetime objects to ISO format strings
    if metadata.get('firstObsTime'):
        metadata['firstObsTime'] = metadata['firstObsTime'].isoformat()
    if metadata.get('lastObsTime'):
        metadata['lastObsTime'] = metadata['lastObsTime'].isoformat()
    
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
        # Join observation types with commas and wrap at 60 characters
        obs_str = ', '.join(obs_types)
        # Split into lines of max 60 characters
        obs_lines = [obs_str[i:i+60] for i in range(0, len(obs_str), 60)]
        print(f"  {constellation}: {obs_lines[0]}")
        for line in obs_lines[1:]:
            print(f"     {line}")
    
    # Print time information
    print("\nTime Information:")
    print(f"  First Observation: {metadata.get('firstObsTime', 'N/A')}")
    print(f"  Last Observation: {metadata.get('lastObsTime', 'N/A')}")
    print(f"  Interval: {metadata.get('interval', 'N/A')} seconds")

def main():
    """
    Main function to demonstrate the RINEX 2 parser.
    """
    # Example file path (replace with an actual file path)
    rinex_file = os.path.join("data", "obs", "ajac0010.22o")
    
    # Check if the file exists
    if not os.path.exists(rinex_file):
        print(f"File not found: {rinex_file}")
        print("Please provide a valid RINEX 2 observation file path.")
        return
    
    # Process the file
    output_dir = "data/jsonpqt"
    metadata_file, parquet_file = process_rinex_file(rinex_file, output_dir)
    
    # Print metadata summary
    print_metadata_summary(metadata_file)
    
    # Alternatively, process all RINEX 2 files in a directory
    # rinex_dir = "rinex_data"
    # rinex_files = find_rinex2_files(rinex_dir)
    # for rinex_file in rinex_files:
    #     process_rinex_file(rinex_file, output_dir)

if __name__ == "__main__":
    main()