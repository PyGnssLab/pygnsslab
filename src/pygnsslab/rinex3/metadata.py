"""
Metadata handling module for RINEX 3 files.
Provides functions to extract, format, and save header metadata.
"""

import json
import os
from pathlib import Path

def extract_metadata(rinex_header):
    """
    Extract and format metadata from RINEX header.
    
    Parameters:
    -----------
    rinex_header : dict
        Dictionary containing RINEX header information
    
    Returns:
    --------
    dict
        Formatted metadata dictionary
    """
    metadata = {
        'rinexVersion': rinex_header.get('rinexVersion'),
        'stationName': rinex_header.get('stationName'),
        'approxPos': rinex_header.get('approxPos'),
        'receiverNumber': rinex_header.get('receiverNumber'),
        'receiverType': rinex_header.get('receiverType'),
        'receiverVersion': rinex_header.get('receiverVersion'),
        'antennaNumber': rinex_header.get('antennaNumber'),
        'antennaType': rinex_header.get('antennaType'),
        'observationTypes': dict(rinex_header.get('observationTypes', {}))
    }
    
    return metadata

def save_metadata(metadata, output_file):
    """
    Save metadata to a JSON file.
    
    Parameters:
    -----------
    metadata : dict
        Metadata dictionary
    output_file : str
        Path to the output JSON file
    
    Returns:
    --------
    str
        Path to the output JSON file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_dir = output_path.parent
    os.makedirs(output_dir, exist_ok=True)
    
    # Write metadata to JSON
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return output_file

def load_metadata(metadata_file):
    """
    Load metadata from a JSON file.
    
    Parameters:
    -----------
    metadata_file : str
        Path to the metadata JSON file
    
    Returns:
    --------
    dict
        Metadata dictionary
    """
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    return metadata

def compare_metadata(metadata1, metadata2):
    """
    Compare two metadata dictionaries and return their differences.
    
    Parameters:
    -----------
    metadata1 : dict
        First metadata dictionary
    metadata2 : dict
        Second metadata dictionary
    
    Returns:
    --------
    dict
        Dictionary of differences
    """
    differences = {}
    
    # Compare simple key-value pairs
    for key in set(metadata1.keys()) | set(metadata2.keys()):
        if key == 'observationTypes':
            continue  # Handle separately
        
        if key not in metadata1:
            differences[key] = {'in_metadata1': None, 'in_metadata2': metadata2[key]}
        elif key not in metadata2:
            differences[key] = {'in_metadata1': metadata1[key], 'in_metadata2': None}
        elif metadata1[key] != metadata2[key]:
            differences[key] = {'in_metadata1': metadata1[key], 'in_metadata2': metadata2[key]}
    
    # Compare observation types
    if 'observationTypes' in metadata1 and 'observationTypes' in metadata2:
        obs_types1 = metadata1['observationTypes']
        obs_types2 = metadata2['observationTypes']
        
        obs_diff = {}
        
        # Check constellations in both
        for const in set(obs_types1.keys()) | set(obs_types2.keys()):
            if const not in obs_types1:
                obs_diff[const] = {'in_metadata1': None, 'in_metadata2': obs_types2[const]}
            elif const not in obs_types2:
                obs_diff[const] = {'in_metadata1': obs_types1[const], 'in_metadata2': None}
            elif set(obs_types1[const]) != set(obs_types2[const]):
                # Find differences in observation types
                only_in_1 = set(obs_types1[const]) - set(obs_types2[const])
                only_in_2 = set(obs_types2[const]) - set(obs_types1[const])
                
                obs_diff[const] = {
                    'only_in_metadata1': list(only_in_1) if only_in_1 else None,
                    'only_in_metadata2': list(only_in_2) if only_in_2 else None
                }
        
        if obs_diff:
            differences['observationTypes'] = obs_diff
    
    return differences