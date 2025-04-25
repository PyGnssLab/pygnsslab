"""
Metadata for RINEX Navigation files.

This module provides metadata and constants related to RINEX Navigation files
and GNSS systems.
"""

from typing import Dict, List, Tuple

# GNSS System Identifiers
GNSS_SYSTEMS = {
    'G': 'GPS',
    'R': 'GLONASS',
    'E': 'Galileo',
    'C': 'BeiDou',
    'J': 'QZSS',
    'I': 'IRNSS/NavIC',
    'S': 'SBAS'
}

# File Type Identifiers
FILE_TYPES = {
    'N': 'GPS Navigation Data',
    'G': 'GLONASS Navigation Data',
    'H': 'GEO Navigation Data',
    'B': 'SBAS Broadcast Data',
    'L': 'GALILEO Navigation Data',
    'P': 'Mixed GNSS Navigation Data',
    'Q': 'QZSS Navigation Data',
    'C': 'BDS Navigation Data',
    'I': 'IRNSS Navigation Data'
}

# RINEX Version Compatibility
RINEX_VERSIONS = {
    2.0: ["GPS", "GLONASS"],
    2.1: ["GPS", "GLONASS"],
    2.11: ["GPS", "GLONASS"],
    2.12: ["GPS", "GLONASS"],
    3.0: ["GPS", "GLONASS", "Galileo", "SBAS", "QZSS"],
    3.01: ["GPS", "GLONASS", "Galileo", "SBAS", "QZSS"],
    3.02: ["GPS", "GLONASS", "Galileo", "SBAS", "QZSS", "BeiDou"],
    3.03: ["GPS", "GLONASS", "Galileo", "SBAS", "QZSS", "BeiDou", "IRNSS"],
    3.04: ["GPS", "GLONASS", "Galileo", "SBAS", "QZSS", "BeiDou", "IRNSS"],
    4.0: ["GPS", "GLONASS", "Galileo", "SBAS", "QZSS", "BeiDou", "IRNSS"]
}

# Navigation Data Record Structure by GNSS System
# Key: System identifier
# Value: List of parameter names in order of appearance
NAV_DATA_STRUCTURE = {
    'G': [  # GPS Navigation Message
        'IODE', 'Crs', 'Delta_n', 'M0',
        'Cuc', 'e', 'Cus', 'sqrt_A',
        'Toe', 'Cic', 'OMEGA', 'Cis',
        'i0', 'Crc', 'omega', 'OMEGA_DOT',
        'IDOT', 'L2_codes', 'GPS_week', 'L2_P_flag',
        'SV_accuracy', 'SV_health', 'TGD', 'IODC',
        'Transmission_time', 'Fit_interval'
    ],
    'R': [  # GLONASS Navigation Message
        'Tau', 'Gamma', 'tb', 'X',
        'X_velocity', 'X_acceleration', 'health', 'Y',
        'Y_velocity', 'Y_acceleration', 'frequency_number', 'Z',
        'Z_velocity', 'Z_acceleration', 'Age'
    ],
    'E': [  # Galileo Navigation Message
        'IODnav', 'Crs', 'Delta_n', 'M0',
        'Cuc', 'e', 'Cus', 'sqrt_A',
        'Toe', 'Cic', 'OMEGA', 'Cis',
        'i0', 'Crc', 'omega', 'OMEGA_DOT',
        'IDOT', 'Data_sources', 'GAL_week', 'SISA',
        'SV_health', 'BGD_E5a_E1', 'BGD_E5b_E1', 'Transmission_time'
    ],
    'C': [  # BeiDou Navigation Message
        'AODE', 'Crs', 'Delta_n', 'M0',
        'Cuc', 'e', 'Cus', 'sqrt_A',
        'Toe', 'Cic', 'OMEGA', 'Cis',
        'i0', 'Crc', 'omega', 'OMEGA_DOT',
        'IDOT', 'spare1', 'BDT_week', 'spare2',
        'SV_accuracy', 'SatH1', 'TGD1', 'TGD2',
        'Transmission_time', 'AODC'
    ],
    'J': [  # QZSS Navigation Message (similar to GPS)
        'IODE', 'Crs', 'Delta_n', 'M0',
        'Cuc', 'e', 'Cus', 'sqrt_A',
        'Toe', 'Cic', 'OMEGA', 'Cis',
        'i0', 'Crc', 'omega', 'OMEGA_DOT',
        'IDOT', 'L2_codes', 'GPS_week', 'L2_P_flag',
        'SV_accuracy', 'SV_health', 'TGD', 'IODC',
        'Transmission_time', 'Fit_interval'
    ],
    'I': [  # IRNSS Navigation Message
        'IODEC', 'Crs', 'Delta_n', 'M0',
        'Cuc', 'e', 'Cus', 'sqrt_A',
        'Toe', 'Cic', 'OMEGA', 'Cis',
        'i0', 'Crc', 'omega', 'OMEGA_DOT',
        'IDOT', 'spare', 'IRNSS_week', 'spare',
        'SV_accuracy', 'SV_health', 'TGD', 'spare',
        'Transmission_time', 'spare'
    ],
    'S': [  # SBAS Navigation Message
        'spare', 'Crs', 'Delta_n', 'M0',
        'Cuc', 'e', 'Cus', 'sqrt_A',
        'Toe', 'Cic', 'OMEGA', 'Cis',
        'i0', 'Crc', 'omega', 'OMEGA_DOT',
        'IDOT', 'spare', 'GPS_week', 'spare',
        'SV_accuracy', 'SV_health', 'spare', 'spare',
        'Transmission_time', 'spare'
    ]
}

# Physical Constants
PHYSICAL_CONSTANTS = {
    'c': 299792458.0,  # Speed of light in vacuum (m/s)
    'mu_earth': 3.986005e14,  # Earth's gravitational constant (m^3/s^2)
    'omega_e': 7.2921151467e-5,  # Earth's rotation rate (rad/s)
    'F': -4.442807633e-10,  # Relativistic correction constant (-2*sqrt(mu)/(c^2))
    'earth_radius': 6371000  # Earth's mean radius (m)
}

# Time System Offsets
TIME_SYSTEM_OFFSETS = {
    # (From, To): Offset in seconds
    ('GPST', 'UTC'): lambda week, tow: leap_seconds(week, tow) - 19,  # GPS Time to UTC
    ('GLST', 'UTC'): lambda week, tow: 0,  # GLONASS Time (UTC-based) to UTC
    ('GST', 'UTC'): lambda week, tow: leap_seconds(week, tow) - 19,  # Galileo System Time to UTC
    ('BDT', 'UTC'): lambda week, tow: leap_seconds(week, tow) - 33,  # BeiDou Time to UTC
    ('QZSST', 'UTC'): lambda week, tow: leap_seconds(week, tow) - 19,  # QZSS Time to UTC
    ('IRNWT', 'UTC'): lambda week, tow: leap_seconds(week, tow) - 19,  # IRNSS Time to UTC
}

# Epoch reference times for different GNSS systems
EPOCH_REFERENCES = {
    'G': (1980, 1, 6, 0, 0, 0),  # GPS: January 6, 1980 00:00:00 UTC
    'R': (1996, 1, 1, 0, 0, 0),  # GLONASS: January 1, 1996 00:00:00 UTC
    'E': (1999, 8, 22, 0, 0, 0),  # Galileo: August 22, 1999 00:00:00 UTC
    'C': (2006, 1, 1, 0, 0, 0),  # BeiDou: January 1, 2006 00:00:00 UTC
    'J': (1980, 1, 6, 0, 0, 0),  # QZSS: Same as GPS
    'I': (1980, 1, 6, 0, 0, 0),  # IRNSS: Same as GPS
    'S': (1980, 1, 6, 0, 0, 0)   # SBAS: Same as GPS
}

def leap_seconds(gps_week, tow):
    """
    Get the number of leap seconds for a given GPS time.
    
    Parameters
    ----------
    gps_week : int
        GPS week number.
    tow : float
        Time of week in seconds.
        
    Returns
    -------
    int
        Number of leap seconds.
    
    Notes
    -----
    GPS time is ahead of UTC by a number of leap seconds that increases over time.
    This function provides a rough estimate based on known leap second insertions.
    For precise applications, use an up-to-date leap second table.
    """
    # Convert GPS week and ToW to seconds since GPS epoch
    seconds_since_gps_epoch = gps_week * 604800 + tow
    
    # Define leap second insertion times in seconds since GPS epoch
    leap_second_insertions = [
        (46828800, 1),    # July 1, 1981
        (78364801, 2),    # July 1, 1982
        (109900802, 3),   # July 1, 1983
        (173059203, 4),   # July 1, 1985
        (252028804, 5),   # January 1, 1988
        (315187205, 6),   # January 1, 1990
        (346723206, 7),   # January 1, 1991
        (393984007, 8),   # July 1, 1992
        (425520008, 9),   # July 1, 1993
        (457056009, 10),  # July 1, 1994
        (504489610, 11),  # January 1, 1996
        (551750411, 12),  # July 1, 1997
        (599184012, 13),  # January 1, 1999
        (820108813, 14),  # January 1, 2006
        (914803214, 15),  # January 1, 2009
        (1025136015, 16), # July 1, 2012
        (1119744016, 17), # July 1, 2015
        (1167264017, 18), # January 1, 2017
        # Add more as they occur
    ]
    
    # Find the number of leap seconds at the given time
    leap_seconds = 0
    for insertion_time, num_leaps in leap_second_insertions:
        if seconds_since_gps_epoch >= insertion_time:
            leap_seconds = num_leaps
        else:
            break
    
    return leap_seconds