# pygnsslab.io.rinex2 Module Documentation

## Overview

The `pygnsslab.io.rinex2` module is a Python package designed for parsing, processing, and manipulating RINEX 2 observation files. RINEX (Receiver Independent Exchange Format) is a standardized format for GNSS (Global Navigation Satellite System) data. This module provides a comprehensive set of tools for extracting metadata and observation data from RINEX 2 files, converting between different time formats, and saving processed data to more efficient formats.

The module is part of the larger `pygnsslab` package and is located at `./src/pygnsslab/io/rinex2`.

## Module Structure

The `pygnsslab.io.rinex2` module consists of the following Python files:

- `__init__.py`: Main module initialization that exports key functionality
- `reader.py`: Contains the `Rinex2Reader` class for parsing RINEX 2 files
- `writer.py`: Functions for saving observation data to parquet format
- `metadata.py`: Functions for handling RINEX metadata
- `utils.py`: Utility functions for time conversions and file operations
- `example_usage.py`: Example script demonstrating how to use the module

## Key Components

### Rinex2Reader

The `Rinex2Reader` class is the primary interface for reading and parsing RINEX 2 observation files.

#### Usage

```python
from pygnsslab.io.rinex2 import Rinex2Reader

# Initialize the reader with a RINEX 2 file
rinex_reader = Rinex2Reader("path/to/rinex_file.o")

# Access metadata
metadata = rinex_reader.metadata

# Access observation data as a pandas DataFrame
obs_data = rinex_reader.get_obs_data()

# Save observation data directly to Parquet (convenience method)
rinex_reader.to_parquet("output.parquet")
```

#### Input

- RINEX 2 observation files (typically with extensions `.obs`, `.o`, `.yyo`, `.yyO`, `.yyN`, or `.yyG`)

#### Output

- `metadata`: Dictionary containing header information from the RINEX file
- `obs_data`: Pandas DataFrame containing observation data

### Metadata Handling

The `metadata.py` module provides functions for extracting, formatting, and saving header metadata from RINEX 2 files.

#### Key Functions

- `extract_metadata(rinex_header)`: Extracts and formats metadata from RINEX header
- `save_metadata(metadata, output_file)`: Saves metadata to a JSON file
- `load_metadata(metadata_file)`: Loads metadata from a JSON file
- `compare_metadata(metadata1, metadata2)`: Compares two metadata dictionaries and returns their differences

#### Usage

```python
from pygnsslab.io.rinex2.metadata import extract_metadata, save_metadata, load_metadata, compare_metadata

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
from pygnsslab.io.rinex2.writer import write_to_parquet, write_obs_summary

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

- `is_rinex2_file(filename)`: Checks if a file is a RINEX 2 observation file
- `find_rinex2_files(directory)`: Finds all RINEX 2 observation files in a directory

#### Usage

```python
from pygnsslab.io.rinex2.utils import datetime_to_mjd, is_rinex2_file, find_rinex2_files
import datetime

# Convert datetime to MJD
dt = datetime.datetime.now()
mjd = datetime_to_mjd(dt)

# Check if a file is a RINEX 2 file
is_rinex2 = is_rinex2_file("path/to/file.o")

# Find all RINEX 2 files in a directory
rinex_files = find_rinex2_files("path/to/directory")
```

## Data Formats

### RINEX 2 Format

The RINEX 2 format is an older standard format for GNSS data, with some notable differences from the newer RINEX 3 format. RINEX 2 observation files contain:

1. **Header Section**: Contains metadata about the observation session, including station information, receiver and antenna details, and observation types.
2. **Observation Section**: Contains the actual observation data from different satellites.

Key differences from RINEX 3:
- Observation types are defined globally rather than per constellation
- Two-digit year format is commonly used
- Limited support for multiple GNSS constellations
- Different formatting for epoch headers and observation data

### Metadata Structure

The extracted metadata from RINEX 2 files is structured as a Python dictionary with the following key fields:

- `rinexVersion`: RINEX version number
- `fileType`: Type of RINEX file (usually 'O' for observation)
- `stationName`: Name of the station
- `observer`: Name of the observer
- `agency`: Agency or institution
- `approxPos`: Approximate position of the station (X, Y, Z coordinates)
- `receiverNumber`: Receiver number
- `receiverType`: Receiver type
- `receiverVersion`: Receiver firmware version
- `antennaNumber`: Antenna number
- `antennaType`: Antenna type
- `observationTypes`: Dictionary of observation types by constellation
  - In RINEX 2, observation types are stored globally but converted to a constellation-based format for compatibility with RINEX 3 processing code
  - Original global list is preserved under the 'ALL' key
- `firstObsTime`: Time of first observation
- `lastObsTime`: Time of last observation
- `interval`: Observation interval in seconds
- `leapSeconds`: Number of leap seconds
- `antennaDelta`: Antenna delta (height, east, north)
- `wavelengthFactors`: Wavelength factors information

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

This structure is designed to be compatible with the RINEX 3 data format for easier integration with existing processing pipelines.

## Example Usage

### Basic Example

```python
from pygnsslab.io.rinex2 import Rinex2Reader
from pygnsslab.io.rinex2.writer import write_to_parquet
import os

# Path to RINEX 2 file
rinex_file = "path/to/rinex_file.o"

# Read RINEX 2 file
rinex_reader = Rinex2Reader(rinex_file)

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
from pygnsslab.io.rinex2 import Rinex2Reader
from pygnsslab.io.rinex2.writer import write_to_parquet
from pygnsslab.io.rinex2.utils import find_rinex2_files
import os

# Find all RINEX 2 files in a directory
rinex_dir = "path/to/rinex_directory"
rinex_files = find_rinex2_files(rinex_dir)

# Process each file
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

for rinex_file in rinex_files:
    # Extract base name
    base_name = os.path.splitext(os.path.basename(rinex_file))[0]
    
    # Read RINEX 2 file
    print(f"Processing {rinex_file}...")
    rinex_reader = Rinex2Reader(rinex_file)
    
    # Get metadata and observations
    metadata = rinex_reader.metadata
    obs_data = rinex_reader.get_obs_data()
    
    # Convert datetime objects to ISO format strings for JSON serialization
    if metadata.get('firstObsTime'):
        metadata['firstObsTime'] = metadata['firstObsTime'].isoformat()
    if metadata.get('lastObsTime'):
        metadata['lastObsTime'] = metadata['lastObsTime'].isoformat()
    
    # Save to parquet format
    parquet_file = os.path.join(output_dir, f"{base_name}.parquet")
    metadata_file = os.path.join(output_dir, f"{base_name}_metadata.json")
    
    # Write to parquet with metadata
    write_to_parquet(obs_data, parquet_file, metadata, metadata_file)
    
    print(f"Saved to {parquet_file} and {metadata_file}")
```

### Comparing Metadata from Multiple Files

```python
from pygnsslab.io.rinex2 import Rinex2Reader
from pygnsslab.io.rinex2.metadata import compare_metadata
import os

# Paths to RINEX 2 files
rinex_file1 = "path/to/rinex_file1.o"
rinex_file2 = "path/to/rinex_file2.o"

# Read RINEX 2 files
rinex_reader1 = Rinex2Reader(rinex_file1)
rinex_reader2 = Rinex2Reader(rinex_file2)

# Get metadata
metadata1 = rinex_reader1.metadata
metadata2 = rinex_reader2.metadata

# Convert datetime objects to strings for comparison
for metadata in [metadata1, metadata2]:
    if metadata.get('firstObsTime'):
        metadata['firstObsTime'] = metadata['firstObsTime'].isoformat()
    if metadata.get('lastObsTime'):
        metadata['lastObsTime'] = metadata['lastObsTime'].isoformat()

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
from pygnsslab.io.rinex2 import Rinex2Reader
import pandas as pd

# Read RINEX 2 file
rinex_reader = Rinex2Reader("path/to/rinex_file.o")
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

# Filter by observation type (has valid pseudorange)
range_data = obs_data[obs_data['range'].notna()]
```

### Analyzing Observation Data

```python
import matplotlib.pyplot as plt
from pygnsslab.io.rinex2 import Rinex2Reader

# Read RINEX 2 file
rinex_reader = Rinex2Reader("path/to/rinex_file.o")
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

# Analyze time coverage
obs_data['mjd_rounded'] = obs_data['mjd'].round(5)  # Round to avoid floating point issues
unique_epochs = obs_data['mjd_rounded'].unique()
print(f"Number of unique epochs: {len(unique_epochs)}")
print(f"First epoch: {unique_epochs.min()}")
print(f"Last epoch: {unique_epochs.max()}")
print(f"Approximate interval: {(unique_epochs[1:] - unique_epochs[:-1]).mean() * 86400:.1f} seconds")
```

### Converting Between RINEX 2 and RINEX 3 Format Data

The module's DataFrame structure is designed to be compatible with the RINEX 3 module, allowing for easy conversion between formats.

```python
from pygnsslab.io.rinex2 import Rinex2Reader
from pygnsslab.io.rinex3.writer import write_to_parquet as write_rinex3

# Read RINEX 2 file
rinex2_reader = Rinex2Reader("path/to/rinex_file.o")
obs_data = rinex2_reader.get_obs_data()
metadata = rinex2_reader.metadata

# Convert datetime objects to strings for JSON serialization
if metadata.get('firstObsTime'):
    metadata['firstObsTime'] = metadata['firstObsTime'].isoformat()
if metadata.get('lastObsTime'):
    metadata['lastObsTime'] = metadata['lastObsTime'].isoformat()

# Save in RINEX 3 compatible format
output_file = "output_rinex3_format.parquet"
metadata_file = "output_rinex3_metadata.json"

# Use the RINEX 3 writer
write_rinex3(obs_data, output_file, metadata, metadata_file)
```

## Handling RINEX 2 Specific Features

### Wavelength Factors

RINEX 2 files may contain wavelength factor information, which is stored in the metadata dictionary.

```python
from pygnsslab.io.rinex2 import Rinex2Reader

# Read RINEX 2 file
rinex_reader = Rinex2Reader("path/to/rinex_file.o")
metadata = rinex_reader.metadata

# Access wavelength factors
wavelength_factors = metadata.get('wavelengthFactors', [])

for wf in wavelength_factors:
    print(f"L1 factor: {wf['L1']}")
    print(f"L2 factor: {wf['L2']}")
    if wf['satellites']:
        print(f"Applies to satellites: {', '.join(wf['satellites'])}")
    else:
        print("Applies to all satellites")
```

### Two-Digit Year Handling

RINEX 2 files often use two-digit years, which are handled by the parser according to the following convention:
- Years 00-79 are interpreted as 2000-2079
- Years 80-99 are interpreted as 1980-1999

```python
from pygnsslab.io.rinex2 import Rinex2Reader

# Read RINEX 2 file with two-digit year
rinex_reader = Rinex2Reader("path/to/rinex_file.99o")  # Year 1999
metadata = rinex_reader.metadata

# Access first observation time (correctly interpreted as 1999)
first_obs = metadata.get('firstObsTime')
print(f"First observation time: {first_obs}")
```

## Limitations and Considerations

1. **Memory Usage**: Processing large RINEX files can be memory-intensive, especially when loading the entire observation dataset into a pandas DataFrame.

2. **File Compatibility**: The module is designed specifically for RINEX 2 format. It may not work correctly with RINEX 1, RINEX 3, or other specialized variations.

3. **Missing Data**: RINEX files may contain missing or corrupted data. The module handles these cases by setting corresponding values to None in the DataFrame.

4. **Performance**: The current implementation prioritizes readability and correctness over performance. For very large files or high-performance applications, additional optimizations may be necessary.

5. **Two-Digit Year Ambiguity**: The RINEX 2 standard uses two-digit years which can be ambiguous. The parser follows the convention that years 00-79 are interpreted as 2000-2079 and years 80-99 are interpreted as 1980-1999.

6. **Constellation Compatibility**: RINEX 2 was developed primarily for GPS observations, with limited support for other GNSS constellations. The module attempts to handle multi-constellation RINEX 2 files, but some specialized constellation-specific data may not be properly parsed.

## Differences Between RINEX 2 and RINEX 3 Handling

The `pygnsslab.io.rinex2` module is designed to work alongside the `pygnsslab.io.rinex3` module, with several key differences in how data is processed:

1. **Observation Types**: 
   - RINEX 2: Observation types are defined globally for all satellites in the header
   - RINEX 3: Observation types are defined per constellation

2. **Time Format**:
   - RINEX 2: Often uses two-digit years with specific epoch line formatting
   - RINEX 3: Uses four-digit years with a different epoch line format

3. **Multi-Constellation Support**:
   - RINEX 2: Limited built-in support for multiple constellations
   - RINEX 3: Full support for multiple GNSS constellations

4. **Compatibility Layer**:
   - The module converts RINEX 2 observation types to a RINEX 3-like structure where they are organized by constellation
   - Original global observation type list is preserved under the 'ALL' key in metadata

## Conclusion

The `pygnsslab.io.rinex2` module provides a comprehensive set of tools for working with RINEX 2 observation files. It enables users to extract metadata, process observation data, convert between different time formats, and save processed data to more efficient file formats. The module is designed to work seamlessly with the RINEX 3 module, allowing for consistent processing of different RINEX version files.