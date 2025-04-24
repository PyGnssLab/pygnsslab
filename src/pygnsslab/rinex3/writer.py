"""
Writer module for saving RINEX observation data to parquet format.
"""

import os
import json
import pandas as pd
from pathlib import Path

def write_to_parquet(obs_data, output_file, metadata=None, metadata_file=None):
    """
    Write observation data to a parquet file and optionally save metadata to a JSON file.
    
    Parameters:
    -----------
    obs_data : pandas.DataFrame
        DataFrame containing observation data
    output_file : str
        Path to the output parquet file
    metadata : dict, optional
        Metadata dictionary to save
    metadata_file : str, optional
        Path to the output metadata JSON file. If None but metadata is provided,
        a default name will be created based on output_file
    
    Returns:
    --------
    tuple
        (parquet_file_path, metadata_file_path)
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_dir = output_path.parent
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure data has the required columns
    required_columns = ['date', 'epoch_sec', 'mjd', 'constellation', 'sat', 
                        'channel', 'range', 'phase', 'doppler', 'snr']
    
    # Create empty columns if they don't exist
    for col in required_columns:
        if col not in obs_data.columns:
            obs_data[col] = None
    
    # Write observation data to parquet
    obs_data.to_parquet(output_file, index=False)
    
    # Write metadata to JSON if provided
    metadata_path = None
    if metadata:
        if not metadata_file:
            # Create default metadata filename
            metadata_file = str(output_path.with_suffix('.json'))
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        metadata_path = metadata_file
    
    return output_file, metadata_path

def write_obs_summary(obs_data, output_file):
    """
    Write a summary of observation data to a text file.
    
    Parameters:
    -----------
    obs_data : pandas.DataFrame
        DataFrame containing observation data
    output_file : str
        Path to the output summary file
    
    Returns:
    --------
    str
        Path to the output summary file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_dir = output_path.parent
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate summary statistics
    summary = {}
    
    # Count observations by constellation
    constellation_counts = obs_data['constellation'].value_counts().to_dict()
    summary['observations_by_constellation'] = constellation_counts
    
    # Count satellites by constellation
    sat_counts = obs_data.groupby('constellation')['sat'].nunique().to_dict()
    summary['satellites_by_constellation'] = sat_counts
    
    # Get date range
    if 'date' in obs_data.columns and not obs_data['date'].empty:
        min_date = obs_data['date'].min()
        max_date = obs_data['date'].max()
        summary['date_range'] = {'start': min_date, 'end': max_date}
    
    # Write summary to file
    with open(output_file, 'w') as f:
        f.write("RINEX Observation Data Summary\n")
        f.write("==============================\n\n")
        
        f.write("Observations by Constellation:\n")
        for const, count in summary.get('observations_by_constellation', {}).items():
            f.write(f"  {const}: {count}\n")
        
        f.write("\nSatellites by Constellation:\n")
        for const, count in summary.get('satellites_by_constellation', {}).items():
            f.write(f"  {const}: {count}\n")
        
        if 'date_range' in summary:
            f.write("\nDate Range:\n")
            f.write(f"  Start: {summary['date_range']['start']}\n")
            f.write(f"  End: {summary['date_range']['end']}\n")
    
    return output_file