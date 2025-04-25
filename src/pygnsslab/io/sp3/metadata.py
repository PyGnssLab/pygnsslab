"""
SP3 metadata classes.

This module contains classes to represent SP3 file metadata, including
header information, epochs, and satellite records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class SP3Header:
    """Class representing the header of an SP3 file."""
    version: str  # 'c' or 'd'
    file_type: str  # 'P'=position only, 'V'=position and velocity, etc.
    time: datetime  # Start time
    epoch_count: int  # Number of epochs
    data_used: str  # Data used
    coordinate_system: str  # Coordinate system
    orbit_type: str  # Orbit type
    agency: str  # Agency providing the data
    gps_week: int  # GPS week
    seconds_of_week: float  # Seconds of week
    epoch_interval: float  # Interval between epochs in seconds
    mjd: int  # Modified Julian Date
    fractional_day: float  # Fractional part of the day
    num_satellites: int  # Number of satellites
    satellite_ids: List[str] = field(default_factory=list)  # List of satellite IDs
    satellite_accuracy: Dict[str, int] = field(default_factory=dict)  # Dictionary of satellite accuracy values
    file_system: str = ""  # File system
    time_system: str = ""  # Time system
    base_pos_vel: List[float] = field(default_factory=list)  # Base position/velocity
    base_clock: List[float] = field(default_factory=list)  # Base clock
    custom_parameters: List[str] = field(default_factory=list)  # Custom parameters
    comments: List[str] = field(default_factory=list)  # Comments


@dataclass
class SP3SatelliteRecord:
    """Class representing a satellite record in an SP3 file."""
    sat_id: str  # Satellite ID (e.g., 'G01')
    x: float  # X coordinate in km
    y: float  # Y coordinate in km
    z: float  # Z coordinate in km
    clock: float  # Clock in microseconds
    x_sdev: Optional[float] = None  # Standard deviation of X in m
    y_sdev: Optional[float] = None  # Standard deviation of Y in m
    z_sdev: Optional[float] = None  # Standard deviation of Z in m
    clock_sdev: Optional[float] = None  # Standard deviation of clock in 1E-12 s
    x_vel: Optional[float] = None  # X velocity in dm/s
    y_vel: Optional[float] = None  # Y velocity in dm/s
    z_vel: Optional[float] = None  # Z velocity in dm/s
    clock_rate: Optional[float] = None  # Clock rate in 1E-14 s/s
    x_vel_sdev: Optional[float] = None  # Standard deviation of X velocity
    y_vel_sdev: Optional[float] = None  # Standard deviation of Y velocity
    z_vel_sdev: Optional[float] = None  # Standard deviation of Z velocity
    clock_rate_sdev: Optional[float] = None  # Standard deviation of clock rate
    correlation: Optional[Dict[str, float]] = None  # Correlation information
    event_flag: Optional[int] = None  # Event flag
    clock_event_flag: Optional[int] = None  # Clock event flag


@dataclass
class SP3Epoch:
    """Class representing an epoch in an SP3 file."""
    time: datetime  # Epoch time
    satellites: Dict[str, SP3SatelliteRecord] = field(default_factory=dict)  # Dictionary of satellite records