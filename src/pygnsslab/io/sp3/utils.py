"""
Utility functions for SP3 file handling.

This module provides utility functions for processing SP3 files,
including format detection and conversion helpers.
"""

import re
from datetime import datetime, timedelta
from typing import Tuple


def identify_sp3_version(first_line: str) -> str:
    """
    Identify the version of an SP3 file from its first line.

    Parameters
    ----------
    first_line : str
        The first line of the SP3 file.

    Returns
    -------
    str
        The SP3 version ('c' or 'd').

    Raises
    ------
    ValueError
        If the first line is not a valid SP3 header line.
    """
    if not first_line.startswith('#'):
        raise ValueError("Not a valid SP3 file: header must start with '#'")
    
    version = first_line[1]  # Second character is the version
    
    if version not in ['c', 'd']:
        raise ValueError(f"Unsupported SP3 version: {version}")
    
    return version


def parse_sp3_datetime(year: int, month: int, day: int, hour: int, minute: int, second: float) -> datetime:
    """
    Parse SP3 date and time components into a datetime object.

    Parameters
    ----------
    year : int
        Year.
    month : int
        Month.
    day : int
        Day.
    hour : int
        Hour.
    minute : int
        Minute.
    second : float
        Second (can include fractional part).

    Returns
    -------
    datetime
        The parsed datetime object.
    """
    int_second = int(second)
    microsecond = int((second - int_second) * 1_000_000)
    
    return datetime(year, month, day, hour, minute, int_second, microsecond)


def compute_mjd(dt: datetime) -> Tuple[int, float]:
    """
    Compute Modified Julian Date and fractional day from a datetime.

    Parameters
    ----------
    dt : datetime
        The datetime object.

    Returns
    -------
    Tuple[int, float]
        The MJD and fractional day.
    """
    # Julian date at January 1, 4713 BCE at noon
    jd = (dt.toordinal() + 1721425.5 +
          (dt.hour - 12) / 24.0 +
          dt.minute / 1440.0 +
          dt.second / 86400.0 +
          dt.microsecond / 86400000000.0)
    
    # Modified Julian Date (MJD = JD - 2400000.5)
    mjd = jd - 2400000.5
    
    # Extract integer and fractional parts
    mjd_int = int(mjd)
    mjd_frac = mjd - mjd_int
    
    return mjd_int, mjd_frac


def gps_time_from_datetime(dt: datetime) -> Tuple[int, float]:
    """
    Convert datetime to GPS week and seconds of week.

    Parameters
    ----------
    dt : datetime
        The datetime object.

    Returns
    -------
    Tuple[int, float]
        The GPS week and seconds of week.
    """
    # GPS time epoch: January 6, 1980 00:00:00 UTC
    gps_epoch = datetime(1980, 1, 6)
    
    # Calculate time difference
    delta = dt - gps_epoch
    
    # Calculate GPS week
    gps_week = delta.days // 7
    
    # Calculate seconds of week
    seconds_of_week = (delta.days % 7) * 86400 + delta.seconds + delta.microseconds / 1_000_000
    
    return gps_week, seconds_of_week


def datetime_from_gps_time(week: int, sow: float) -> datetime:
    """
    Convert GPS week and seconds of week to datetime.

    Parameters
    ----------
    week : int
        GPS week number.
    sow : float
        Seconds of week.

    Returns
    -------
    datetime
        The corresponding datetime object.
    """
    # GPS time epoch: January 6, 1980 00:00:00 UTC
    gps_epoch = datetime(1980, 1, 6)
    
    # Calculate time from GPS epoch
    delta = timedelta(weeks=week, seconds=sow)
    
    return gps_epoch + delta


def parse_satellite_id(sat_id: str) -> Tuple[str, int]:
    """
    Parse a satellite ID into system and number.

    Parameters
    ----------
    sat_id : str
        The satellite ID (e.g., 'G01').

    Returns
    -------
    Tuple[str, int]
        The satellite system and PRN/slot number.
    """
    if len(sat_id) < 2:
        raise ValueError(f"Invalid satellite ID: {sat_id}")
    
    system = sat_id[0]
    number = int(sat_id[1:])
    
    return system, number


def format_satellite_id(system: str, number: int) -> str:
    """
    Format a satellite system and number into a satellite ID.

    Parameters
    ----------
    system : str
        The satellite system (e.g., 'G').
    number : int
        The PRN/slot number.

    Returns
    -------
    str
        The formatted satellite ID (e.g., 'G01').
    """
    return f"{system}{number:02d}"