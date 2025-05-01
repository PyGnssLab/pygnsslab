# pygnsslab.io.rinex3 Module Documentation

## Overview

The `pygnsslab.io.rinex3` module is a Python package designed for parsing, processing, and manipulating RINEX 3 observation files. RINEX (Receiver Independent Exchange Format) is a standard format for GNSS (Global Navigation Satellite System) data. This module provides tools for extracting metadata and observation data from RINEX 3 files, converting between different time formats, and saving processed data to more efficient formats.

## Module Structure

The `pygnsslab.io.rinex3` module consists of the following Python files:

- `__init__.py`: Main module initialization that exports key functionality
- `reader.py`: Contains the `Rinex3Reader` class for parsing RINEX 3 files
- `writer.py`: Functions for saving observation data to parquet format
- `metadata.py`: Functions for handling RINEX metadata
- `utils.py`: Utility functions for time conversions and file operations
- `example_usage.py`: Example script demonstrating how to use the module

## Installation

The module is part of the `pygnsslab` package and is located at `./src/pygnsslab/io/rinex3`. To use it, you need to install the `pygnsslab` package.

## Key Components

### Rinex3Reader

The `Rinex3Reader` class is the primary interface for reading and parsing RINEX 3 observation files.

#### Usage

```python
from pygnsslab.io.rinex3 import Rinex3Reader

# Initialize the reader with a RINEX 3 file
rinex_reader = Rinex3Reader("path/to/rinex_file.rnx")

# Access metadata
metadata = rinex_reader.metadata

# Access observation data as a pandas DataFrame
obs_data = rinex_reader.get_obs_data()
```

#### Input

- RINEX 3 observation files (typically with extensions `.rnx`, `.crx`, or `.obs`)

#### Output

- `metadata`: Dictionary containing header information from the RINEX file
- `obs_data`: Pandas DataFrame containing observation data

### Metadata Handling

The `metadata.py` module provides functions for extracting, formatting, and saving header metadata from RINEX 3 files.

#### Key Functions

- `extract_metadata(rinex_header)`: Extracts and formats metadata from RINEX header
- `save_metadata(metadata, output_file)`: Saves metadata to a JSON file
- `load_metadata(metadata_file)`: Loads metadata from a JSON file
- `compare_metadata(metadata1, metadata2)`: Compares two metadata dictionaries and returns their differences

#### Usage

```python
from pygnsslab.io.rinex3.metadata import extract_metadata, save_metadata, load_metadata, compare_metadata

# Extract metadata from RINEX header
metadata = extract_metadata(rinex_header)

# Save metadata to a JSON file
save_metadata(metadata, "output_metadata.json")

# Load metadata from a JSON file
loaded_metadata = load_metadata("metadata.json")

# Compare two metadata dictionaries
differences = compare_metadata(metadata1, metadata2)
```

### Data Writing

The `writer.py` module provides functions for saving RINEX observation data to parquet format and creating summary reports.

#### Key Functions

- `write_to_parquet(obs_data, output_file, metadata=None, metadata_file=None)`: Writes observation data to a parquet file and optionally saves metadata
- `write_obs_summary(obs_data, output_file)`: Writes a summary of observation data to a text file

#### Usage

```python
from pygnsslab.io.rinex3.writer import write_to_parquet, write_obs_summary

# Write observation data to parquet format
parquet_file, metadata_file = write_to_parquet(obs_data, "output.parquet", metadata)

# Write observation data summary
summary_file = write_obs_summary(obs_data, "summary.txt")
```

### Utility Functions

The `utils.py` module provides utility functions for time conversions and file operations.

#### Time Conversion Functions

- `datetime_to_mjd(dt)`: Converts a datetime object to Modified Julian Date (MJD)
- `datetime_to_jd(dt)`: Converts a datetime object to Julian Date
- `mjd_to_datetime(mjd)`: Converts Modified Julian Date to datetime object
- `jd_to_datetime(jd)`: Converts Julian Date to datetime object
- `time_to_seconds_of_day(time_obj)`: Converts a time object to seconds of day

#### File Operations

- `is_rinex3_file(filename)`: Checks if a file is a RINEX 3 observation file
- `find_rinex3_files(directory)`: Finds all RINEX 3 observation files in a directory

#### Usage

```python
from pygnsslab.io.rinex3.utils import datetime_to_mjd, is_rinex3_file, find_rinex3_files
import datetime

# Convert datetime to MJD
dt = datetime.datetime.now()
mjd = datetime_to_mjd(dt)

# Check if a file is a RINEX 3 file
is_rinex3 = is_rinex3_file("path/to/file.rnx")

# Find all RINEX 3 files in a directory
rinex_files = find_rinex3_files("path/to/directory")
```

## Data Formats

### RINEX 3 Format

The RINEX 3 format is a standard format for GNSS data. RINEX 3 observation files contain:

1. **Header Section**: Contains metadata about the observation session, including station information, receiver and antenna details, and observation types.
2. **Observation Section**: Contains the actual observation data from different satellites and constellations.

### Metadata Structure

The extracted metadata from RINEX 3 files is structured as a Python dictionary with the following key fields:

- `rinexVersion`: RINEX version number
- `stationName`: Name of the station
- `approxPos`: Approximate position of the station (X, Y, Z coordinates)
- `receiverNumber`: Receiver number
- `receiverType`: Receiver type
- `receiverVersion`: Receiver firmware version
- `antennaNumber`: Antenna number
- `antennaType`: Antenna type
- `observationTypes`: Dictionary of observation types by constellation

### Observation Data Structure

The observation data is structured as a pandas DataFrame with the following columns:

- `date`: Observation date
- `epoch_sec`: Seconds of day
- `mjd`: Modified Julian Date
- `constellation`: GNSS constellation (G=GPS, R=GLONASS, E=Galileo, C=BeiDou, J=QZSS, S=SBAS)
- `sat`: Satellite identifier
- `channel`: Signal channel/frequency
- `range`: Pseudorange measurement
- `phase`: Carrier phase measurement
- `doppler`: Doppler measurement
- `snr`: Signal-to-noise ratio

## Example Usage

### Basic Example

```python
from pygnsslab.io.rinex3 import Rinex3Reader
from pygnsslab.io.rinex3.writer import write_to_parquet
import os

# Path to RINEX 3 file
rinex_file = "path/to/rinex_file.rnx"

# Read RINEX 3 file
rinex_reader = Rinex3Reader(rinex_file)

# Get metadata and observations
metadata = rinex_reader.metadata
obs_data = rinex_reader.get_obs_data()

# Save to parquet format
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)
base_name = os.path.splitext(os.path.basename(rinex_file))[0]
parquet_file = os.path.join(output_dir, f"{base_name}.parquet")
metadata_file = os.path.join(output_dir, f"{base_name}_metadata.json")

# Write to parquet with metadata
write_to_parquet(obs_data, parquet_file, metadata, metadata_file)
```

### Processing Multiple Files

```python
from pygnsslab.io.rinex3 import Rinex3Reader
from pygnsslab.io.rinex3.writer import write_to_parquet
from pygnsslab.io.rinex3.utils import find_rinex3_files
import os

# Find all RINEX 3 files in a directory
rinex_dir = "path/to/rinex_directory"
rinex_files = find_rinex3_files(rinex_dir)

# Process each file
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

for rinex_file in rinex_files:
    # Extract base name
    base_name = os.path.splitext(os.path.basename(rinex_file))[0]
    
    # Read RINEX 3 file
    print(f"Processing {rinex_file}...")
    rinex_reader = Rinex3Reader(rinex_file)
    
    # Get metadata and observations
    metadata = rinex_reader.metadata
    obs_data = rinex_reader.get_obs_data()
    
    # Save to parquet format
    parquet_file = os.path.join(output_dir, f"{base_name}.parquet")
    metadata_file = os.path.join(output_dir, f"{base_name}_metadata.json")
    
    # Write to parquet with metadata
    write_to_parquet(obs_data, parquet_file, metadata, metadata_file)
    
    print(f"Saved to {parquet_file} and {metadata_file}")
```

### Comparing Metadata from Multiple Files

```python
from pygnsslab.io.rinex3 import Rinex3Reader
from pygnsslab.io.rinex3.metadata import compare_metadata
import os

# Paths to RINEX 3 files
rinex_file1 = "path/to/rinex_file1.rnx"
rinex_file2 = "path/to/rinex_file2.rnx"

# Read RINEX 3 files
rinex_reader1 = Rinex3Reader(rinex_file1)
rinex_reader2 = Rinex3Reader(rinex_file2)

# Get metadata
metadata1 = rinex_reader1.metadata
metadata2 = rinex_reader2.metadata

# Compare metadata
differences = compare_metadata(metadata1, metadata2)

# Print differences
if differences:
    print("Differences found in metadata:")
    for key, diff in differences.items():
        print(f"  {key}: {diff}")
else:
    print("No differences found in metadata")
```

## Advanced Usage

### Filtering Observation Data

```python
from pygnsslab.io.rinex3 import Rinex3Reader
import pandas as pd

# Read RINEX 3 file
rinex_reader = Rinex3Reader("path/to/rinex_file.rnx")
obs_data = rinex_reader.get_obs_data()

# Filter by constellation (e.g., GPS only)
gps_data = obs_data[obs_data['constellation'] == 'G']

# Filter by satellite
sat_data = obs_data[obs_data['sat'] == 'G01']

# Filter by time range
start_mjd = 59000.0
end_mjd = 59001.0
time_filtered_data = obs_data[(obs_data['mjd'] >= start_mjd) & (obs_data['mjd'] <= end_mjd)]

# Filter by signal quality (SNR > 30)
quality_data = obs_data[obs_data['snr'] > 30]
```

### Analyzing Observation Data

```python
import matplotlib.pyplot as plt
from pygnsslab.io.rinex3 import Rinex3Reader

# Read RINEX 3 file
rinex_reader = Rinex3Reader("path/to/rinex_file.rnx")
obs_data = rinex_reader.get_obs_data()

# Group by constellation and count satellites
sat_counts = obs_data.groupby('constellation')['sat'].nunique()
print("Satellites by constellation:")
print(sat_counts)

# Plot satellite counts
sat_counts.plot(kind='bar')
plt.title('Number of Satellites by Constellation')
plt.xlabel('Constellation')
plt.ylabel('Number of Satellites')
plt.grid(True)
plt.savefig('satellite_counts.png')

# Analyze SNR distribution
plt.figure()
obs_data['snr'].hist(bins=20)
plt.title('SNR Distribution')
plt.xlabel('SNR')
plt.ylabel('Frequency')
plt.grid(True)
plt.savefig('snr_distribution.png')
```

## Limitations and Considerations

1. **Memory Usage**: Processing large RINEX files can be memory-intensive, especially when loading the entire observation dataset into a pandas DataFrame.

2. **File Compatibility**: The module is designed specifically for RINEX 3 format. It may not work correctly with RINEX 2 or other variations.

3. **Missing Data**: RINEX files may contain missing or corrupted data. The module handles these cases by setting corresponding values to None in the DataFrame.

4. **Performance**: The current implementation prioritizes readability and correctness over performance. For very large files or high-performance applications, additional optimizations may be necessary.

## Conclusion

The `pygnsslab.io.rinex3` module provides a comprehensive set of tools for working with RINEX 3 observation files. It enables users to extract metadata, process observation data, and convert between different time formats and file formats. With its intuitive API and versatile functionality, it serves as a valuable resource for GNSS data processing and analysis.