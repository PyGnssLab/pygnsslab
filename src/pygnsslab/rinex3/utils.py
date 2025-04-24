"""
Utility functions for RINEX 3 processing.
"""

import datetime
import numpy as np
import os
from pathlib import Path

def datetime_to_mjd(dt):
    """
    Convert a datetime object to Modified Julian Date (MJD).
    
    Parameters:
    -----------
    dt : datetime.datetime
        Datetime object to convert
    
    Returns:
    --------
    float
        Modified Julian Date
    """
    # Convert to Julian date first
    jd = datetime_to_jd(dt)
    # Convert Julian date to Modified Julian Date
    mjd = jd - 2400000.5
    
    return mjd

def datetime_to_jd(dt):
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

def mjd_to_datetime(mjd):
    """
    Convert Modified Julian Date (MJD) to datetime object.
    
    Parameters:
    -----------
    mjd : float
        Modified Julian Date
    
    Returns:
    --------
    datetime.datetime
        Datetime object
    """
    # Convert MJD to Julian date
    jd = mjd + 2400000.5
    
    # Convert Julian date to datetime
    return jd_to_datetime(jd)

def jd_to_datetime(jd):
    """
    Convert Julian date to datetime object.
    
    Parameters:
    -----------
    jd : float
        Julian date
    
    Returns:
    --------
    datetime.datetime
        Datetime object
    """
    jd = jd + 0.5  # Shift by 0.5 day
    
    # Calculate integer and fractional parts
    F, I = np.modf(jd)
    I = int(I)
    
    A = np.trunc((I - 1867216.25) / 36524.25)
    B = I + 1 + A - np.trunc(A / 4)
    
    C = B + 1524
    D = np.trunc((C - 122.1) / 365.25)
    E = np.trunc(365.25 * D)
    G = np.trunc((C - E) / 30.6001)
    
    # Calculate day, month, year
    day = C - E + F - np.trunc(30.6001 * G)
    
    if G < 13.5:
        month = G - 1
    else:
        month = G - 13
        
    if month > 2.5:
        year = D - 4716
    else:
        year = D - 4715
    
    # Calculate time
    day_frac = day - int(day)
    hours = int(day_frac * 24)
    minutes = int((day_frac * 24 - hours) * 60)
    seconds = ((day_frac * 24 - hours) * 60 - minutes) * 60
    
    # Create datetime object
    try:
        dt = datetime.datetime(
            int(year), 
            int(month), 
            int(day), 
            hours, 
            minutes, 
            int(seconds), 
            int((seconds - int(seconds)) * 1e6)
        )
        return dt
    except ValueError:
        # Handling edge cases
        if int(day) == 0:
            # Handle case where day is calculated as 0
            month = int(month) - 1
            if month == 0:
                month = 12
                year = int(year) - 1
            days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            # Adjust for leap year
            if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                day = 29
            else:
                day = days_in_month[month]
        else:
            day = int(day)
        
        return datetime.datetime(
            int(year), 
            int(month), 
            day, 
            hours, 
            minutes, 
            int(seconds), 
            int((seconds - int(seconds)) * 1e6)
        )

def time_to_seconds_of_day(time_obj):
    """
    Convert a time object to seconds of day.
    
    Parameters:
    -----------
    time_obj : datetime.time
        Time object to convert
    
    Returns:
    --------
    float
        Seconds of day
    """
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1e6

def is_rinex3_file(filename):
    """
    Check if a file is a RINEX 3 observation file.
    
    Parameters:
    -----------
    filename : str
        Path to the file
    
    Returns:
    --------
    bool
        True if the file is a RINEX 3 observation file, False otherwise
    """
    if not os.path.exists(filename):
        return False
    
    # Check file extension
    ext = Path(filename).suffix.lower()
    if ext not in ['.rnx', '.crx', '.obs']:
        # Not a standard RINEX observation file extension
        return False
    
    # Check file content
    try:
        with open(filename, 'r') as f:
            # Read first few lines
            header_lines = [f.readline() for _ in range(10)]
            
            # Check for RINEX 3 version marker
            for line in header_lines:
                if "RINEX VERSION / TYPE" in line and line.strip().startswith("3"):
                    return True
    except:
        # If there's an error reading the file, assume it's not a valid RINEX file
        return False
    
    return False

def find_rinex3_files(directory):
    """
    Find all RINEX 3 observation files in a directory.
    
    Parameters:
    -----------
    directory : str
        Path to the directory
    
    Returns:
    --------
    list
        List of paths to RINEX 3 observation files
    """
    rinex_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_rinex3_file(filepath):
                rinex_files.append(filepath)
    
    return rinex_files