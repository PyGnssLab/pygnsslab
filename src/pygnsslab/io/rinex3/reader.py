"""
RINEX 3 reader module for parsing observation files.
"""

import os
import re
import datetime
import json
import numpy as np
import pandas as pd
from collections import defaultdict

class Rinex3Reader:
    """
    Class for reading and parsing RINEX 3 observation files.
    """
    
    def __init__(self, filename):
        """
        Initialize the Rinex3Reader with a RINEX 3 observation file.
        
        Parameters:
        -----------
        filename : str
            Path to the RINEX 3 observation file
        """
        self.filename = filename
        self.header = {}
        self.obs_data = []
        self.metadata = {}
        self._parse_file()
    
    def _parse_file(self):
        """
        Parse the RINEX 3 file, extracting header information and observation data.
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
        Parse the header section of the RINEX file.
        
        Parameters:
        -----------
        header_lines : list
            List of strings containing the header section
        """
        # Initialize header data structures
        self.header = {
            'rinexVersion': None,
            'stationName': None,
            'approxPos': [None, None, None],
            'receiverNumber': None,
            'receiverType': None,
            'receiverVersion': None,
            'antennaNumber': None,
            'antennaType': None,
            'observationTypes': defaultdict(list)
        }
        
        # Parse each header line
        for line in header_lines:
            label = line[60:].strip()
            
            # RINEX Version / Type
            if "RINEX VERSION / TYPE" in label:
                self.header['rinexVersion'] = line[:9].strip()
            
            # Marker Name
            elif "MARKER NAME" in label:
                self.header['stationName'] = line[:60].strip()
            
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
            
            # Observation types
            elif "SYS / # / OBS TYPES" in label:
                constellation = line[0].strip()
                if not constellation:
                    # Continuation line
                    last_constellation = list(self.header['observationTypes'].keys())[-1]
                    obs_types = [line[i:i+4].strip() for i in range(7, 60, 4) if line[i:i+4].strip() and i+4 <= 60]
                    self.header['observationTypes'][last_constellation].extend(obs_types)
                else:
                    # New constellation
                    obs_types = [line[i:i+4].strip() for i in range(7, 60, 4) if line[i:i+4].strip() and i+4 <= 60]
                    self.header['observationTypes'][constellation] = obs_types
        
        # Convert metadata to the required format
        self.metadata = self.header.copy()
    
    def _parse_observations(self, observation_lines):
        """
        Parse the observation section of the RINEX file.
        
        Parameters:
        -----------
        observation_lines : list
            List of strings containing the observation section
        """
        # Preallocation - start with a reasonable capacity
        initial_capacity = 100000
        
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
        
        i = 0
        
        while i < len(observation_lines):
            line = observation_lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Check if this is an epoch line (starts with ">")
            if line.startswith(">"):
                try:
                    # Parse epoch information
                    year = int(line[2:6])
                    month = int(line[7:9])
                    day = int(line[10:12])
                    hour = int(line[13:15])
                    minute = int(line[16:18])
                    second = float(line[19:30])
                    epoch_flag = int(line[31:32])
                    num_sats = int(line[32:35])
                    
                    # Skip special epochs (flags > 1)
                    if epoch_flag > 1:
                        i += 1
                        while i < len(observation_lines) and not observation_lines[i].startswith(">"):
                            i += 1
                        continue
                    
                    epoch_datetime = datetime.datetime(year, month, day, hour, minute, int(second))
                    epoch_date = epoch_datetime.date().isoformat()
                    epoch_sec = hour * 3600 + minute * 60 + second
                    
                    # Calculate Modified Julian Date (MJD)
                    jd = self._datetime_to_jd(epoch_datetime)
                    mjd = jd - 2400000.5
                    
                    # Move to next line to start processing satellites
                    i += 1
                    
                    # Parse and process satellites
                    sat_count = 0
                    sat_lines = []
                    
                    # Collect satellite lines (could span multiple lines)
                    while sat_count < num_sats and i < len(observation_lines):
                        line = observation_lines[i]
                        if line.startswith(">"):
                            break
                            
                        # If first character is a constellation identifier, it's a satellite line
                        if line and line[0] in "GRECJS":
                            sat_lines.append(line)
                            sat_count += 1
                            
                        i += 1
                        
                    # Process each satellite
                    for sat_line in sat_lines:
                        # Extract satellite ID (first 3 characters)
                        if len(sat_line) >= 3:
                            sat_id = sat_line[0:3].strip()
                            if not sat_id:
                                continue
                                
                            constellation = sat_id[0]
                            
                            # Get observation types for this constellation
                            obs_types = self.header['observationTypes'].get(constellation, [])
                            num_obs = len(obs_types)
                            
                            if num_obs == 0:
                                continue
                                
                            # Initialize data structures
                            unique_channels = {}  # Maps channel code to index
                            channel_data = {}     # Stores observation data by channel
                            
                            # Process this satellite's observations
                            for obs_idx in range(num_obs):
                                # Calculate position in the line
                                # Each observation takes 16 characters (14 for value, 2 for LLI and signal strength)
                                # First 3 characters are for satellite ID
                                line_idx = obs_idx // 5  # 5 observations per line
                                pos_in_line = obs_idx % 5
                                
                                start_pos = 3 + pos_in_line * 16  # Starting at position 3 (after satellite ID)
                                
                                # Check if we need to read from next lines
                                curr_line = sat_line
                                if line_idx > 0:
                                    # Need to read from continuation lines
                                    line_offset = i - len(sat_lines) + line_idx
                                    if line_offset < len(observation_lines):
                                        curr_line = observation_lines[line_offset]
                                    else:
                                        continue
                                
                                # Skip if line is too short
                                if len(curr_line) <= start_pos:
                                    continue
                                
                                # Extract observation value
                                end_pos = start_pos + 14
                                if end_pos > len(curr_line):
                                    end_pos = len(curr_line)
                                
                                obs_str = curr_line[start_pos:end_pos].strip()
                                obs_value = None
                                if obs_str:
                                    try:
                                        obs_value = float(obs_str)
                                    except ValueError:
                                        obs_value = None
                                
                                # Skip if no valid observation
                                if obs_value is None:
                                    continue
                                
                                # Extract SNR (signal strength)
                                snr_value = None
                                if end_pos + 2 <= len(curr_line):
                                    snr_str = curr_line[end_pos:end_pos+2].strip()
                                    if snr_str:
                                        try:
                                            snr_value = float(snr_str)
                                        except ValueError:
                                            snr_value = None
                                
                                # Get observation type and channel
                                obs_type = obs_types[obs_idx]
                                
                                if len(obs_type) >= 2:
                                    # First character is observation type (C, L, D, S)
                                    obs_code = obs_type[0]
                                    # Rest is the channel code
                                    channel_code = obs_type[1:]
                                    
                                    # Get or create channel index
                                    if channel_code not in unique_channels:
                                        unique_channels[channel_code] = len(unique_channels)
                                        channel_data[channel_code] = {
                                            'range': None,
                                            'phase': None,
                                            'doppler': None,
                                            'snr': None
                                        }
                                    
                                    # Map observation type to appropriate category
                                    if obs_code == 'C':  # Pseudorange
                                        channel_data[channel_code]['range'] = obs_value
                                    elif obs_code == 'L':  # Carrier phase
                                        channel_data[channel_code]['phase'] = obs_value
                                    elif obs_code == 'D':  # Doppler
                                        channel_data[channel_code]['doppler'] = obs_value
                                    elif obs_code == 'S':  # Signal strength
                                        channel_data[channel_code]['snr'] = obs_value
                                        
                                    # If we have a separate SNR value, use it regardless of observation type
                                    if snr_value is not None:
                                        channel_data[channel_code]['snr'] = snr_value
                            
                            # Add data for each channel to our lists
                            for channel_code, data in channel_data.items():
                                dates.append(epoch_date)
                                epoch_secs.append(epoch_sec)
                                mjds.append(mjd)
                                constellations.append(constellation)
                                sats.append(sat_id)
                                channels.append(channel_code)
                                ranges.append(data['range'])
                                phases.append(data['phase'])
                                dopplers.append(data['doppler'])
                                snrs.append(data['snr'])
                
                except Exception as e:
                    # Handle parsing errors
                    print(f"Error parsing epoch: {str(e)}")
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
        })

    
    # Note: This method is no longer used with the improved parsing approach
    
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