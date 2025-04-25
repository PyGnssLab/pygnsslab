"""
RINEX 2 reader module for parsing observation files.
"""

import os
import re
import datetime
import json
import numpy as np
import pandas as pd
from collections import defaultdict

class Rinex2Reader:
    """
    Class for reading and parsing RINEX 2 observation files.
    """
    
    def __init__(self, filename):
        """
        Initialize the Rinex2Reader with a RINEX 2 observation file.
        
        Parameters:
        -----------
        filename : str
            Path to the RINEX 2 observation file
        """
        self.filename = filename
        self.header = {}
        self.obs_data = []
        self.metadata = {}
        self._parse_file()
    
    def _parse_file(self):
        """
        Parse the RINEX 2 file, extracting header information and observation data.
        """
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"RINEX file not found: {self.filename}")
        
        # Read the entire file
        with open(self.filename, 'r') as f:
            lines = f.readlines()
        
        # Determine where the header ends (look for END OF HEADER marker)
        header_end_idx = 0
        for i, line in enumerate(lines):
            if "END OF HEADER" in line:
                header_end_idx = i
                break
        
        # Extract header and observation sections
        header_lines = lines[:header_end_idx + 1]
        observation_lines = lines[header_end_idx + 1:]
        
        # Parse header
        self._parse_header(header_lines)
        
        # Parse observations
        self._parse_observations(observation_lines)
    
    def _parse_header(self, header_lines):
        """
        Parse the header section of the RINEX 2 file.
        
        Parameters:
        -----------
        header_lines : list
            List of strings containing the header section
        """
        # Initialize header data structures
        self.header = {
            'rinexVersion': None,
            'fileType': None,
            'stationName': None,
            'observer': None,
            'agency': None,
            'approxPos': [None, None, None],
            'receiverNumber': None,
            'receiverType': None,
            'receiverVersion': None,
            'antennaNumber': None,
            'antennaType': None,
            'observationTypes': [],  # In RINEX 2, observation types are a single list, not grouped by constellation
            'firstObsTime': None,
            'lastObsTime': None,
            'interval': None,
            'leapSeconds': None,
            'antennaDelta': [None, None, None],  # Height, East, North
            'wavelengthFactors': []
        }
        
        # Parse each header line
        for line in header_lines:
            if len(line) < 60:  # Ensure line is long enough to have a label
                continue
                
            label = line[60:].strip()
            
            # RINEX Version / Type
            if "RINEX VERSION / TYPE" in label:
                self.header['rinexVersion'] = line[:9].strip()
                self.header['fileType'] = line[20:21].strip()
                
            # Marker Name
            elif "MARKER NAME" in label:
                self.header['stationName'] = line[:60].strip()
                
            # Observer / Agency
            elif "OBSERVER / AGENCY" in label:
                self.header['observer'] = line[:20].strip()
                self.header['agency'] = line[20:60].strip()
                
            # Approx Position XYZ
            elif "APPROX POSITION XYZ" in label:
                try:
                    x = float(line[:14].strip())
                    y = float(line[14:28].strip())
                    z = float(line[28:42].strip())
                    self.header['approxPos'] = [x, y, z]
                except ValueError:
                    pass
                    
            # Receiver info
            elif "REC # / TYPE / VERS" in label:
                self.header['receiverNumber'] = line[:20].strip()
                self.header['receiverType'] = line[20:40].strip()
                self.header['receiverVersion'] = line[40:60].strip()
                
            # Antenna info
            elif "ANT # / TYPE" in label:
                self.header['antennaNumber'] = line[:20].strip()
                self.header['antennaType'] = line[20:40].strip()
                
            # Antenna Delta H/E/N
            elif "ANTENNA: DELTA H/E/N" in label:
                try:
                    h = float(line[:14].strip())
                    e = float(line[14:28].strip())
                    n = float(line[28:42].strip())
                    self.header['antennaDelta'] = [h, e, n]
                except ValueError:
                    pass
                
            # Observation types
            elif "# / TYPES OF OBSERV" in label:
                if not self.header['observationTypes']:  # Only process number if we haven't started collecting types
                    try:
                        num_obs = int(line[:6].strip())
                    except ValueError:
                        continue
                    
                    # Read observation types from this line (up to 9 per line)
                    types_in_this_line = []
                    for j in range(9):
                        start_idx = 6 + j * 6
                        if start_idx + 6 <= len(line):
                            obs_type = line[start_idx:start_idx+6].strip()
                            if obs_type:
                                types_in_this_line.append(obs_type)
                    
                    self.header['observationTypes'].extend(types_in_this_line)
                    
                    # If we need to read continuation lines
                    remaining_types = num_obs - len(types_in_this_line)
                    line_index = 1
                    
                    while remaining_types > 0 and line_index < len(header_lines):
                        # Look for continuation lines with more observation types
                        if "# / TYPES OF OBSERV" in header_lines[line_index+header_lines.index(line)][60:].strip():
                            cont_line = header_lines[line_index+header_lines.index(line)]
                            types_in_cont_line = []
                            
                            # Skip the first 6 characters (continuation lines don't have number)
                            for j in range(9):
                                start_idx = 6 + j * 6
                                if start_idx + 6 <= len(cont_line):
                                    obs_type = cont_line[start_idx:start_idx+6].strip()
                                    if obs_type:
                                        types_in_cont_line.append(obs_type)
                            
                            self.header['observationTypes'].extend(types_in_cont_line)
                            remaining_types -= len(types_in_cont_line)
                            line_index += 1
                        else:
                            break
            
            # Wavelength Factors
            elif "WAVELENGTH FACT L1/2" in label:
                try:
                    factor_l1 = int(line[:6].strip())
                    factor_l2 = int(line[6:12].strip())
                    num_sats = int(line[12:18].strip())
                    
                    # Read satellite list if specified
                    sat_list = []
                    if num_sats > 0:
                        for i in range(num_sats):
                            if i >= 7:  # Max 7 satellites per line
                                break
                            sat_idx = 18 + i * 3
                            if sat_idx + 3 <= len(line):
                                sat = line[sat_idx:sat_idx+3].strip()
                                if sat:
                                    sat_list.append(sat)
                    
                    self.header['wavelengthFactors'].append({
                        'L1': factor_l1,
                        'L2': factor_l2,
                        'satellites': sat_list if num_sats > 0 else []
                    })
                except ValueError:
                    pass
            
            # Time of first observation
            elif "TIME OF FIRST OBS" in label:
                try:
                    year = int(line[:6].strip())
                    # Handle 2-digit year in RINEX 2
                    if year < 80:
                        year += 2000
                    elif year < 100:
                        year += 1900
                        
                    month = int(line[6:12].strip())
                    day = int(line[12:18].strip())
                    hour = int(line[18:24].strip())
                    minute = int(line[24:30].strip())
                    second = float(line[30:36].strip())
                    
                    self.header['firstObsTime'] = datetime.datetime(
                        year, month, day, hour, minute, int(second), 
                        int((second - int(second)) * 1000000)
                    )
                except (ValueError, IndexError):
                    pass
            
            # Time of last observation
            elif "TIME OF LAST OBS" in label:
                try:
                    year = int(line[:6].strip())
                    # Handle 2-digit year in RINEX 2
                    if year < 80:
                        year += 2000
                    elif year < 100:
                        year += 1900
                        
                    month = int(line[6:12].strip())
                    day = int(line[12:18].strip())
                    hour = int(line[18:24].strip())
                    minute = int(line[24:30].strip())
                    second = float(line[30:36].strip())
                    
                    self.header['lastObsTime'] = datetime.datetime(
                        year, month, day, hour, minute, int(second),
                        int((second - int(second)) * 1000000)
                    )
                except (ValueError, IndexError):
                    pass
            
            # Interval between observations
            elif "INTERVAL" in label:
                try:
                    self.header['interval'] = float(line[:10].strip())
                except ValueError:
                    pass
            
            # Leap seconds
            elif "LEAP SECONDS" in label:
                try:
                    self.header['leapSeconds'] = int(line[:6].strip())
                except ValueError:
                    pass
        
        # Convert metadata to the required format
        self.metadata = self.header.copy()
        
        # Add observationTypes as a dictionary for compatibility with existing code
        # RINEX 2 observation types are not grouped by constellation in the file,
        # but for compatibility we'll put them all under the 'ALL' constellation
        if self.header['observationTypes']:
            self.metadata['observationTypes'] = {'ALL': self.header['observationTypes']}
    
    def _parse_observations(self, observation_lines):
        """
        Parse the observation section of the RINEX 2 file.
        
        Parameters:
        -----------
        observation_lines : list
            List of strings containing the observation section
        """
        # Data arrays for each column
        dates = []
        epoch_secs = []
        mjds = []
        constellations = []
        sats = []
        channels = []
        ranges = []
        phases = []
        dopplers = []
        snrs = []
        # We'll still parse these but not include them in the final DataFrame
        llis = []  # Loss of Lock Indicators
        strengths = []  # Signal strengths
        
        # Get observation types - in RINEX 2, these are global for all satellite systems
        obs_types = self.header['observationTypes']
        
        # Track the unique observation types actually used by each constellation
        constellation_obs_types = defaultdict(set)
        
        i = 0
        while i < len(observation_lines):
            line = observation_lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # In RINEX 2, an epoch line starts with a space and has the year in columns 2-3
            # Format: " yy mm dd hh mm ss.ssss  f  nnn"
            if line[0] == " " and len(line) >= 3 and line[1:3].strip().isdigit():
                try:
                    # Parse epoch header
                    year = int(line[1:3])
                    # Adjust 2-digit year to 4-digit
                    if year < 80:
                        year += 2000
                    elif year < 100:
                        year += 1900
                        
                    month = int(line[4:6])
                    day = int(line[7:9])
                    hour = int(line[10:12])
                    minute = int(line[13:15])
                    second = float(line[16:26])
                    epoch_flag = int(line[28:30].strip())
                    num_sats = int(line[30:32])
                    
                    # Skip special epochs (flags > 1)
                    if epoch_flag > 1:
                        # Skip event specific records
                        i += 1
                        skip_lines = (num_sats // 12) + (1 if num_sats % 12 > 0 else 0)
                        i += skip_lines
                        continue
                    
                    epoch_datetime = datetime.datetime(year, month, day, hour, minute, int(second))
                    epoch_date = epoch_datetime.date().isoformat()
                    epoch_sec = hour * 3600 + minute * 60 + second
                    
                    # Calculate Modified Julian Date (MJD)
                    jd = self._datetime_to_jd(epoch_datetime)
                    mjd = jd - 2400000.5
                    
                    # Parse satellite list
                    sat_ids = []
                    for j in range(min(12, num_sats)):  # Max 12 sats per line
                        # In RINEX 2, satellite IDs are in format "snn" (s=system character, nn=number)
                        start_idx = 32 + j * 3
                        if start_idx + 3 <= len(line):
                            sat_id = line[start_idx:start_idx+3].strip()
                            if sat_id:
                                # Add system identifier if missing
                                if len(sat_id) == 2 and sat_id.isdigit():
                                    sat_id = 'G' + sat_id  # Default to GPS if not specified
                                elif len(sat_id) == 1:
                                    sat_id = sat_id + '0'  # Handle single digit sats
                                sat_ids.append(sat_id)
                    
                    # Handle continuation lines for satellite list
                    sat_lines_needed = (num_sats - 1) // 12 + 1
                    sat_line_idx = 1
                    
                    while len(sat_ids) < num_sats and sat_line_idx < sat_lines_needed:
                        if i + sat_line_idx >= len(observation_lines):
                            break
                        
                        cont_line = observation_lines[i + sat_line_idx]
                        sats_this_line = min(12, num_sats - len(sat_ids))
                        
                        for j in range(sats_this_line):
                            start_idx = 32 + j * 3
                            if start_idx + 3 <= len(cont_line):
                                sat_id = cont_line[start_idx:start_idx+3].strip()
                                if sat_id:
                                    # Add system identifier if missing
                                    if len(sat_id) == 2 and sat_id.isdigit():
                                        sat_id = 'G' + sat_id  # Default to GPS if not specified
                                    elif len(sat_id) == 1:
                                        sat_id = sat_id + '0'  # Handle single digit sats
                                    sat_ids.append(sat_id)
                        
                        sat_line_idx += 1
                    
                    # Move to first observation record
                    i += sat_line_idx
                    
                    # Process observations for each satellite
                    for sat_idx, sat_id in enumerate(sat_ids):
                        # Calculate how many lines needed for this satellite
                        # RINEX 2 has 5 observations per line
                        lines_needed = (len(obs_types) - 1) // 5 + 1
                        
                        # Extract constellation identifier from satellite ID
                        # In RINEX 2, this is typically G for GPS, R for GLONASS
                        constellation = sat_id[0] if len(sat_id) > 0 else 'G'
                        
                        # Process observation lines for this satellite
                        # Create a dict to collect all data for this satellite's channels
                        channel_data = {}
                        
                        for line_idx in range(lines_needed):
                            if i >= len(observation_lines):
                                break
                                
                            obs_line = observation_lines[i]
                            i += 1
                            
                            # Each observation is 16 characters (14 for value, 1 for LLI, 1 for strength)
                            for obs_idx in range(5):  # 5 observations per line in RINEX 2
                                data_idx = line_idx * 5 + obs_idx
                                if data_idx >= len(obs_types):
                                    break
                                
                                obs_type = obs_types[data_idx]
                                start_pos = obs_idx * 16
                                
                                if start_pos + 14 <= len(obs_line):
                                    # Extract value, LLI, and signal strength
                                    value_str = obs_line[start_pos:start_pos+14].strip()
                                    lli_str = obs_line[start_pos+14:start_pos+15].strip() if start_pos+15 <= len(obs_line) else ''
                                    strength_str = obs_line[start_pos+15:start_pos+16].strip() if start_pos+16 <= len(obs_line) else ''
                                    
                                    # Process the value
                                    value = None
                                    lli = None
                                    strength = None
                                    
                                    if value_str:
                                        try:
                                            value = float(value_str)
                                        except ValueError:
                                            pass
                                    
                                    if lli_str:
                                        try:
                                            lli = int(lli_str)
                                        except ValueError:
                                            pass
                                    
                                    if strength_str:
                                        try:
                                            strength = int(strength_str)
                                        except ValueError:
                                            pass
                                    
                                    # Determine observation category and channel
                                    obs_category = None
                                    channel = None
                                    
                                    if obs_type.startswith('C') or obs_type.startswith('P'):
                                        # Pseudorange
                                        obs_category = 'range'
                                        # Handle P1/P2 vs C1/C2 distinction
                                        if obs_type.startswith('P'):
                                            channel = obs_type[1:] + 'P'  # Add 'P' suffix to distinguish from C-type
                                        else:
                                            channel = obs_type[1:]
                                    elif obs_type.startswith('L'):
                                        # Carrier phase
                                        obs_category = 'phase'
                                        channel = obs_type[1:]
                                    elif obs_type.startswith('D'):
                                        # Doppler
                                        obs_category = 'doppler'
                                        channel = obs_type[1:]
                                    elif obs_type.startswith('S'):
                                        # Signal strength
                                        obs_category = 'snr'
                                        channel = obs_type[1:]
                                    
                                    # Skip if no valid observation or can't classify
                                    if obs_category is None or channel is None or value is None:
                                        continue
                                    
                                    # Track which observation types are actually used by this constellation
                                    constellation_obs_types[constellation].add(obs_type)
                                    
                                    # Initialize channel data structure if not already present
                                    if channel not in channel_data:
                                        channel_data[channel] = {
                                            'range': None,
                                            'phase': None,
                                            'doppler': None,
                                            'snr': None
                                        }
                                    
                                    # Store the observation
                                    channel_data[channel][obs_category] = value
                                    
                                    # If we have a separate signal strength value, use it
                                    if obs_category == 'snr' and value is not None:
                                        channel_data[channel]['snr'] = value
                        
                        # Now add data for each channel to our arrays
                        for channel, data in channel_data.items():
                            dates.append(epoch_date)
                            epoch_secs.append(epoch_sec)
                            mjds.append(mjd)
                            constellations.append(constellation)
                            sats.append(sat_id)
                            channels.append(channel)
                            ranges.append(data['range'])
                            phases.append(data['phase'])
                            dopplers.append(data['doppler'])
                            snrs.append(data['snr'])
                
                except Exception as e:
                    # Handle parsing errors
                    print(f"Error parsing epoch at line {i}: {str(e)}")
                    i += 1
            else:
                i += 1
        
        # Create final DataFrame
        self.obs_data = pd.DataFrame({
            'date': dates,
            'epoch_sec': epoch_secs,
            'mjd': mjds,
            'constellation': constellations,
            'sat': sats,
            'channel': channels,
            'range': ranges,
            'phase': phases,
            'doppler': dopplers,
            'snr': snrs
            # lli and strength columns removed as requested
        })
        
        # Update metadata with the observation types actually used by each constellation
        # This provides a more accurate representation than the header, which gives all possible types
        self._update_constellation_observation_types(constellation_obs_types)
    
    def _update_constellation_observation_types(self, constellation_obs_types):
        """
        Update metadata with observation types actually used by each constellation.
        
        Parameters:
        -----------
        constellation_obs_types : dict
            Dictionary mapping constellation to set of observation types used
        """
        # Convert sets to sorted lists
        obs_types_by_constellation = {}
        
        for constellation, obs_set in constellation_obs_types.items():
            # Group observation types by channel
            channel_types = defaultdict(list)
            
            for obs_type in obs_set:
                # Extract the channel
                if obs_type.startswith('C') or obs_type.startswith('P'):
                    channel = obs_type[1:]
                    type_code = obs_type[0]
                    channel_types[channel].append(type_code)
                elif len(obs_type) > 1:
                    channel = obs_type[1:]
                    type_code = obs_type[0]
                    channel_types[channel].append(type_code)
            
            # Create the list of observation types for this constellation
            constellation_types = []
            
            for channel, types in sorted(channel_types.items()):
                for type_code in sorted(['L', 'C', 'P', 'D', 'S']):
                    if type_code in types:
                        constellation_types.append(f"{type_code}{channel}")
            
            obs_types_by_constellation[constellation] = constellation_types
        
        # Update metadata
        self.metadata['observationTypes'] = obs_types_by_constellation
        
        # Keep the original global list under 'ALL'
        if self.header['observationTypes']:
            self.metadata['observationTypes']['ALL'] = self.header['observationTypes']
    
    def _datetime_to_jd(self, dt):
        """
        Convert a datetime object to Julian date.
        
        Parameters:
        -----------
        dt : datetime.datetime
            Datetime object to convert
        
        Returns:
        --------
        float
            Julian date
        """
        # Extract components
        year, month, day = dt.year, dt.month, dt.day
        hour, minute, second = dt.hour, dt.minute, dt.second
        microsecond = dt.microsecond
        
        # Calculate decimal day
        decimal_day = day + (hour / 24.0) + (minute / 1440.0) + ((second + microsecond / 1e6) / 86400.0)
        
        # Calculate Julian date
        if month <= 2:
            year -= 1
            month += 12
        
        A = int(year / 100)
        B = 2 - A + int(A / 4)
        
        jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + decimal_day + B - 1524.5
        
        return jd
    
    def get_metadata_json(self):
        """
        Get the metadata in JSON format.
        
        Returns:
        --------
        str
            Metadata in JSON format
        """
        return json.dumps(self.metadata)
    
    def get_obs_data(self):
        """
        Get the observation data as a DataFrame.
        
        Returns:
        --------
        pandas.DataFrame
            Observation data
        """
        return self.obs_data
    
    def to_parquet(self, output_file):
        """
        Save the observation data to a Parquet file.
        
        Parameters:
        -----------
        output_file : str
            Path to the output Parquet file
            
        Returns:
        --------
        bool
            True if successful, False otherwise
        """
        try:
            # Create a copy of the DataFrame to avoid modifying the original
            df = self.obs_data.copy()
            
            # Ensure all the RINEX3-compatible column names and structure
            df_columns = {
                'date': 'date',
                'epoch_sec': 'epoch_sec',
                'mjd': 'mjd',
                'constellation': 'constellation',
                'sat': 'sat',
                'channel': 'channel',
                'range': 'range',
                'phase': 'phase', 
                'doppler': 'doppler',
                'snr': 'snr'
            }
            
            # Rename columns if needed
            df = df.rename(columns=df_columns)
            
            # Ensure all expected columns exist (add empty ones if missing)
            for col in df_columns.values():
                if col not in df.columns:
                    df[col] = None
                    
            # Save to Parquet format
            df.to_parquet(output_file, index=False)
            
            return True
        except Exception as e:
            print(f"Error saving to Parquet: {str(e)}")
            return False