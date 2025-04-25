"""
SP3 file reader module.

This module provides functionality to read SP3 format files,
supporting both SP3-c and SP3-d formats.
"""

import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Tuple, Union

from .metadata import SP3Epoch, SP3Header, SP3SatelliteRecord
from .utils import (
    identify_sp3_version,
    parse_sp3_datetime,
    parse_satellite_id
)


def safe_int_parse(value_str: str, default: int = 0) -> int:
    """
    Safely parse a string to integer, handling empty strings and invalid values.
    
    Parameters
    ----------
    value_str : str
        The string to parse.
    default : int, optional
        Default value to return if parsing fails, by default 0
        
    Returns
    -------
    int
        The parsed integer or default value.
    """
    try:
        # Clean the string by removing non-digit characters except for minus sign
        # and strip any leading/trailing whitespace
        cleaned_str = value_str.strip()
        if not cleaned_str:
            return default
        
        # Remove any trailing periods or commas if they exist
        if cleaned_str.endswith('.') or cleaned_str.endswith(','):
            cleaned_str = cleaned_str[:-1]
            
        return int(cleaned_str)
    except (ValueError, TypeError):
        return default


def safe_float_parse(value_str: str, default: float = 0.0) -> float:
    """
    Safely parse a string to float, handling empty strings and invalid values.
    
    Parameters
    ----------
    value_str : str
        The string to parse.
    default : float, optional
        Default value to return if parsing fails, by default 0.0
        
    Returns
    -------
    float
        The parsed float or default value.
    """
    try:
        # Clean the string and strip any leading/trailing whitespace
        cleaned_str = value_str.strip()
        if not cleaned_str:
            return default
            
        return float(cleaned_str)
    except (ValueError, TypeError):
        return default


class SP3Reader:
    """
    Reader for SP3 (Standard Product 3) precise orbit files.
    
    This class can read both SP3-c and SP3-d format files.
    """
    
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize the SP3 reader.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the SP3 file.
        """
        self.file_path = Path(file_path)
        self.header: Optional[SP3Header] = None
        self.epochs: List[SP3Epoch] = []
        
        # Open and read the file
        self._read_file()
    
    def _read_file(self):
        """
        Read and parse the entire SP3 file.
        """
        with open(self.file_path, 'r') as file:
            self._parse_header(file)
            self._parse_epochs(file)
    
    def _parse_header(self, file: TextIO):
        """
        Parse the SP3 file header.
        
        Parameters
        ----------
        file : TextIO
            Open file handle positioned at the start of the file.
        """
        # Read the first line to determine version
        line = file.readline().rstrip()
        
        version = identify_sp3_version(line)
        
        if version == 'c':
            self._parse_header_c(file, line)
        elif version == 'd':
            self._parse_header_d(file, line)
    
    def _parse_header_c(self, file: TextIO, first_line: str):
        """
        Parse SP3-c format header.
        
        Parameters
        ----------
        file : TextIO
            Open file handle positioned after the first line.
        first_line : str
            The first line of the file.
        """
        # Parse first line content
        version = first_line[1]  # Extract version from the first line
        file_type = first_line[2]
        year = safe_int_parse(first_line[3:7])
        month = safe_int_parse(first_line[8:10])
        day = safe_int_parse(first_line[11:13])
        hour = safe_int_parse(first_line[14:16])
        minute = safe_int_parse(first_line[17:19])
        second = safe_float_parse(first_line[20:31])
        epoch_count = safe_int_parse(first_line[32:39])
        data_used = first_line[40:45]
        coordinate_system = first_line[46:51]
        orbit_type = first_line[52:55]
        agency = first_line[56:60]
        
        # Create datetime object
        time = parse_sp3_datetime(year, month, day, hour, minute, second)
        
        # Parse second line for GPS week and seconds
        line = file.readline().rstrip()
        gps_week = safe_int_parse(line[3:7])
        seconds_of_week = safe_float_parse(line[8:23])
        epoch_interval = safe_float_parse(line[24:38])
        mjd = safe_int_parse(line[39:44].strip('.,'))
        fractional_day = safe_float_parse(line[45:60])
        
        # Initialize satellite list
        num_satellites = safe_int_parse(first_line[60:62])
        satellite_ids = []
        
        # Read satellite IDs (next lines starting with '+')
        # Each '+' line can contain up to 17 satellite IDs
        remaining_sats = num_satellites
        while remaining_sats > 0:
            line = file.readline().rstrip()
            if not line.startswith('+'):
                break
                
            # Extract satellite IDs (each is 3 characters)
            for i in range(1, min(remaining_sats + 1, 18)):
                sat_id = line[i*3:i*3+3].strip()
                if sat_id:
                    satellite_ids.append(sat_id)
            
            remaining_sats -= 17
        
        # Read satellite accuracy (lines starting with '++')
        satellite_accuracy = {}
        sat_index = 0
        while sat_index < num_satellites:
            line = file.readline().rstrip()
            if not line.startswith('++'):
                break
                
            # Each accuracy value is 3 characters
            for i in range(min(17, num_satellites - sat_index)):
                try:
                    acc_value = safe_int_parse(line[i*3+3:i*3+6])
                    if sat_index + i < len(satellite_ids):
                        satellite_accuracy[satellite_ids[sat_index + i]] = acc_value
                except (ValueError, IndexError):
                    # Skip if we can't parse the accuracy
                    pass
            
            sat_index += 17
        
        # Read file system and time system
        # Initialize with default values
        file_system = "G"  # Default to GPS
        time_system = "GPS"  # Default to GPS
        
        line = file.readline().rstrip()
        if line.startswith('%c'):
            file_system = line[3:5]
            time_system = line[9:12]
        
        # Skip remaining header lines
        comments = []  # Initialize comments list
        while True:
            line = file.readline().rstrip()
            if line.startswith('/*'):
                comments.append(line[2:].strip())
            elif line.startswith('*'):
                break  # End of header
            else:
                # Skip other header lines
                pass
        
        # Create header object
        self.header = SP3Header(
            version=version,
            file_type=file_type,
            time=time,
            epoch_count=epoch_count,
            data_used=data_used,
            coordinate_system=coordinate_system,
            orbit_type=orbit_type,
            agency=agency,
            gps_week=gps_week,
            seconds_of_week=seconds_of_week,
            epoch_interval=epoch_interval,
            mjd=mjd,
            fractional_day=fractional_day,
            num_satellites=num_satellites,
            satellite_ids=satellite_ids,
            satellite_accuracy=satellite_accuracy,
            file_system=file_system,
            time_system=time_system,
            comments=comments
        )
    
    def _parse_header_d(self, file: TextIO, first_line: str):
        """
        Parse SP3-d format header.
        
        Parameters
        ----------
        file : TextIO
            Open file handle positioned after the first line.
        first_line : str
            The first line of the file.
        """
        # Parse first line content (similar to SP3-c but with minor differences)
        version = first_line[1]  # Extract version from the first line
        file_type = first_line[2]
        year = safe_int_parse(first_line[3:7])
        month = safe_int_parse(first_line[8:10])
        day = safe_int_parse(first_line[11:13])
        hour = safe_int_parse(first_line[14:16])
        minute = safe_int_parse(first_line[17:19])
        second = safe_float_parse(first_line[20:31])
        epoch_count = safe_int_parse(first_line[32:39])
        data_used = first_line[40:45]
        coordinate_system = first_line[46:51]
        orbit_type = first_line[52:55]
        agency = first_line[56:60]
        
        # Create datetime object
        time = parse_sp3_datetime(year, month, day, hour, minute, second)
        
        # Parse second line for GPS week and seconds
        line = file.readline().rstrip()
        gps_week = safe_int_parse(line[3:7])
        seconds_of_week = safe_float_parse(line[8:23])
        epoch_interval = safe_float_parse(line[24:38])
        mjd = safe_int_parse(line[39:44].strip('.,'))
        fractional_day = safe_float_parse(line[45:60])
        
        # Initialize satellite list
        num_satellites = safe_int_parse(first_line[60:62])
        satellite_ids = []
        
        # Read satellite IDs (next lines starting with '+')
        # Each '+' line can contain up to 17 satellite IDs
        remaining_sats = num_satellites
        while remaining_sats > 0:
            line = file.readline().rstrip()
            if not line.startswith('+'):
                break
                
            # Extract satellite IDs (each is 3 characters)
            for i in range(1, min(remaining_sats + 1, 18)):
                sat_id = line[i*3:i*3+3].strip()
                if sat_id:
                    satellite_ids.append(sat_id)
            
            remaining_sats -= 17
        
        # Read satellite accuracy (lines starting with '++')
        satellite_accuracy = {}
        sat_index = 0
        while sat_index < num_satellites:
            line = file.readline().rstrip()
            if not line.startswith('++'):
                break
                
            # Each accuracy value is 3 characters
            for i in range(min(17, num_satellites - sat_index)):
                try:
                    acc_value = safe_int_parse(line[i*3+3:i*3+6])
                    if sat_index + i < len(satellite_ids):
                        satellite_accuracy[satellite_ids[sat_index + i]] = acc_value
                except (ValueError, IndexError):
                    # Skip if we can't parse the accuracy
                    pass
            
            sat_index += 17
        
        # Read file system and time system
        # Initialize with default values
        file_system = "G"  # Default to GPS
        time_system = "GPS"  # Default to GPS
        
        line = file.readline().rstrip()
        if line.startswith('%c'):
            file_system = line[3:5]
            time_system = line[9:12]
        
        # Skip remaining header lines
        comments = []  # Initialize comments list
        while True:
            line = file.readline().rstrip()
            if line.startswith('/*'):
                comments.append(line[2:].strip())
            elif line.startswith('*'):
                break  # End of header
            else:
                # Skip other header lines
                pass
        
        # Create header object
        self.header = SP3Header(
            version=version,
            file_type=file_type,
            time=time,
            epoch_count=epoch_count,
            data_used=data_used,
            coordinate_system=coordinate_system,
            orbit_type=orbit_type,
            agency=agency,
            gps_week=gps_week,
            seconds_of_week=seconds_of_week,
            epoch_interval=epoch_interval,
            mjd=mjd,
            fractional_day=fractional_day,
            num_satellites=num_satellites,
            satellite_ids=satellite_ids,
            satellite_accuracy=satellite_accuracy,
            file_system=file_system,
            time_system=time_system,
            comments=comments
        )
    
    def _parse_epochs(self, file: TextIO):
        """
        Parse epoch data.
        
        Parameters
        ----------
        file : TextIO
            Open file handle positioned after the header.
        """
        self.epochs = []
        
        while True:
            line = file.readline().rstrip()
            
            # End of file or end marker
            if not line or "EOF" in line:
                break
                
            # New epoch line
            if line.startswith('*'):
                # Parse epoch time
                year = safe_int_parse(line[3:7])
                month = safe_int_parse(line[8:10])
                day = safe_int_parse(line[11:13])
                hour = safe_int_parse(line[14:16])
                minute = safe_int_parse(line[17:19])
                second = safe_float_parse(line[20:31])
                
                # Create epoch object
                epoch_time = parse_sp3_datetime(year, month, day, hour, minute, second)
                epoch = SP3Epoch(time=epoch_time)
                self.epochs.append(epoch)
                
            # Position record ('P')
            elif line.startswith('P'):
                if not self.epochs:
                    # Skip if no epoch has been defined
                    continue
                
                # Current epoch
                current_epoch = self.epochs[-1]
                
                # Parse position data
                try:
                    # Split the line by whitespace
                    values = line.split()
                    if len(values) >= 5:
                        sat_id = values[0][1:]  # Remove 'P' prefix
                        x = safe_float_parse(values[1])
                        y = safe_float_parse(values[2])
                        z = safe_float_parse(values[3])
                        clock = safe_float_parse(values[4])
                        
                        # Optional event flags
                        event_flag = safe_int_parse(values[5]) if len(values) > 5 else None
                        clock_event_flag = safe_int_parse(values[6]) if len(values) > 6 else None
                        
                        # Create satellite record
                        current_epoch.satellites[sat_id] = SP3SatelliteRecord(
                            sat_id=sat_id,
                            x=x,
                            y=y,
                            z=z,
                            clock=clock,
                            event_flag=event_flag,
                            clock_event_flag=clock_event_flag
                        )
                except (IndexError, ValueError) as e:
                    # Skip if we can't parse the position
                    print(f"Warning: Could not parse position line: {line}")
                    print(f"Error: {e}")
                    continue
            
            # Position standard deviation record ('EP')
            elif line.startswith('EP'):
                if not self.epochs:
                    # Skip if no epoch has been defined
                    continue
                
                # Current epoch
                current_epoch = self.epochs[-1]
                
                # Parse position standard deviation data
                try:
                    # Split the line by whitespace
                    values = line.split()
                    if len(values) >= 5:
                        sat_id = values[0][2:]  # Remove 'EP' prefix
                        x_sdev = safe_float_parse(values[1])
                        y_sdev = safe_float_parse(values[2])
                        z_sdev = safe_float_parse(values[3])
                        clock_sdev = safe_float_parse(values[4])
                        
                        # Update satellite record
                        if sat_id in current_epoch.satellites:
                            sat = current_epoch.satellites[sat_id]
                            sat.x_sdev = x_sdev
                            sat.y_sdev = y_sdev
                            sat.z_sdev = z_sdev
                            sat.clock_sdev = clock_sdev
                except (IndexError, ValueError):
                    # Skip if we can't parse the standard deviation
                    continue
            
            # Velocity record ('V')
            elif line.startswith('V'):
                if not self.epochs:
                    # Skip if no epoch has been defined
                    continue
                
                # Current epoch
                current_epoch = self.epochs[-1]
                
                # Parse velocity data
                try:
                    # Split the line by whitespace
                    values = line.split()
                    if len(values) >= 5:
                        sat_id = values[0][1:]  # Remove 'V' prefix
                        x_vel = safe_float_parse(values[1])
                        y_vel = safe_float_parse(values[2])
                        z_vel = safe_float_parse(values[3])
                        clock_rate = safe_float_parse(values[4])
                        
                        # Update satellite record
                        if sat_id in current_epoch.satellites:
                            sat = current_epoch.satellites[sat_id]
                            sat.x_vel = x_vel
                            sat.y_vel = y_vel
                            sat.z_vel = z_vel
                            sat.clock_rate = clock_rate
                except (IndexError, ValueError):
                    # Skip if we can't parse the velocity
                    continue
            
            # Velocity standard deviation record ('EV')
            elif line.startswith('EV'):
                if not self.epochs:
                    # Skip if no epoch has been defined
                    continue
                
                # Current epoch
                current_epoch = self.epochs[-1]
                
                # Parse velocity standard deviation data
                try:
                    # Split the line by whitespace
                    values = line.split()
                    if len(values) >= 5:
                        sat_id = values[0][2:]  # Remove 'EV' prefix
                        x_vel_sdev = safe_float_parse(values[1])
                        y_vel_sdev = safe_float_parse(values[2])
                        z_vel_sdev = safe_float_parse(values[3])
                        clock_rate_sdev = safe_float_parse(values[4])
                        
                        # Update satellite record
                        if sat_id in current_epoch.satellites:
                            sat = current_epoch.satellites[sat_id]
                            sat.x_vel_sdev = x_vel_sdev
                            sat.y_vel_sdev = y_vel_sdev
                            sat.z_vel_sdev = z_vel_sdev
                            sat.clock_rate_sdev = clock_rate_sdev
                except (IndexError, ValueError):
                    # Skip if we can't parse the standard deviation
                    continue
    
    def get_satellite_positions(self, sat_id: str) -> List[Tuple[datetime, float, float, float, float]]:
        """
        Get all positions and clock corrections for a specific satellite.
        
        Parameters
        ----------
        sat_id : str
            The satellite ID (e.g., 'G01').
        
        Returns
        -------
        List[Tuple[datetime, float, float, float, float]]
            List of tuples containing (time, x, y, z, clock) for each epoch.
        """
        positions = []
        
        for epoch in self.epochs:
            if sat_id in epoch.satellites:
                sat = epoch.satellites[sat_id]
                positions.append((epoch.time, sat.x, sat.y, sat.z, sat.clock))
        
        return positions
    
    def get_satellite_velocities(self, sat_id: str) -> List[Tuple[datetime, float, float, float, float]]:
        """
        Get all velocities and clock rates for a specific satellite.
        
        Parameters
        ----------
        sat_id : str
            The satellite ID (e.g., 'G01').
        
        Returns
        -------
        List[Tuple[datetime, float, float, float, float]]
            List of tuples containing (time, x_vel, y_vel, z_vel, clock_rate) for each epoch.
            Returns empty list if the file does not contain velocity data.
        """
        if not self.header or self.header.file_type != 'V':
            return []
        
        velocities = []
        
        for epoch in self.epochs:
            if sat_id in epoch.satellites:
                sat = epoch.satellites[sat_id]
                if sat.x_vel is not None and sat.y_vel is not None and sat.z_vel is not None:
                    velocities.append((epoch.time, sat.x_vel, sat.y_vel, sat.z_vel, sat.clock_rate))
        
        return velocities
    
    def get_epoch_data(self, epoch_time: datetime) -> Optional[SP3Epoch]:
        """
        Get data for a specific epoch.
        
        Parameters
        ----------
        epoch_time : datetime
            The epoch time.
        
        Returns
        -------
        Optional[SP3Epoch]
            The epoch data if found, None otherwise.
        """
        for epoch in self.epochs:
            # Compare with a small tolerance for floating point differences
            time_diff = abs((epoch.time - epoch_time).total_seconds())
            if time_diff < 0.001:  # Tolerance of 1 millisecond
                return epoch
        
        return None
    
    def get_satellite_positions_at_time(self, sat_id: str, time: datetime) -> Optional[SP3SatelliteRecord]:
        """
        Get satellite position at a specific time.
        
        Parameters
        ----------
        sat_id : str
            The satellite ID (e.g., 'G01').
        time : datetime
            The time for which to get the position.
        
        Returns
        -------
        Optional[SP3SatelliteRecord]
            The satellite record if found, None otherwise.
        """
        epoch = self.get_epoch_data(time)
        if epoch and sat_id in epoch.satellites:
            return epoch.satellites[sat_id]
        
        return None
    
    def get_satellites_at_epoch(self, time: datetime) -> Dict[str, SP3SatelliteRecord]:
        """
        Get all satellite records for a specific epoch.
        
        Parameters
        ----------
        time : datetime
            The epoch time.
        
        Returns
        -------
        Dict[str, SP3SatelliteRecord]
            Dictionary of satellite records for the specified epoch.
            Empty dictionary if the epoch is not found.
        """
        epoch = self.get_epoch_data(time)
        if epoch:
            return epoch.satellites
        
        return {}