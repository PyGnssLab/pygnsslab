"""
Utility functions for RINEX Navigation file handling.

This module provides helper functions for working with RINEX navigation data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional

def gps_time_to_datetime(week: int, seconds: float) -> datetime:
    """
    Convert GPS time (week number + seconds of week) to datetime.
    
    Parameters
    ----------
    week : int
        GPS week number.
    seconds : float
        Seconds of the GPS week.
        
    Returns
    -------
    datetime
        Equivalent datetime object in UTC.
    """
    gps_epoch = datetime(1980, 1, 6, 0, 0, 0)
    delta = timedelta(weeks=week, seconds=seconds)
    return gps_epoch + delta

def datetime_to_gps_time(dt: datetime) -> Tuple[int, float]:
    """
    Convert datetime to GPS time (week number + seconds of week).
    
    Parameters
    ----------
    dt : datetime
        Datetime object in UTC.
        
    Returns
    -------
    Tuple[int, float]
        GPS week number and seconds of the week.
    """
    gps_epoch = datetime(1980, 1, 6, 0, 0, 0)
    delta = dt - gps_epoch
    
    # Total seconds since GPS epoch
    total_seconds = delta.total_seconds()
    
    # GPS week number
    week = int(total_seconds / (7 * 24 * 3600))
    
    # Seconds of the week
    sow = total_seconds % (7 * 24 * 3600)
    
    return week, sow

def interpolate_orbit(nav_data: pd.DataFrame, time: datetime, 
                      sat_system: str = 'G', prn: int = 1) -> Dict[str, float]:
    """
    Interpolate satellite position at a given time using navigation data.
    
    Parameters
    ----------
    nav_data : pd.DataFrame
        Navigation data DataFrame for a specific satellite system.
    time : datetime
        Time at which to interpolate the satellite position.
    sat_system : str, optional
        Satellite system identifier (default: 'G' for GPS).
    prn : int, optional
        Satellite PRN number (default: 1).
        
    Returns
    -------
    Dict[str, float]
        Dictionary containing interpolated position (X, Y, Z) and velocity (VX, VY, VZ).
        
    Notes
    -----
    This is a simplified version that works for GPS satellites.
    Different algorithms are needed for other GNSS systems.
    """
    if sat_system not in ['G', 'J']:  # Only GPS and QZSS supported for now
        raise ValueError(f"Interpolation for {sat_system} not supported yet.")
    
    # Filter navigation data for the specific satellite
    sat_data = nav_data[nav_data['PRN'] == prn].sort_values('Epoch')
    
    if sat_data.empty:
        raise ValueError(f"No navigation data found for {sat_system}{prn:02d}")
    
    # Find the closest epoch before the requested time
    closest_row = sat_data[sat_data['Epoch'] <= time].iloc[-1]
    
    # Extract orbit parameters
    mu = 3.986005e14  # Earth's gravitational constant (m^3/s^2)
    omega_e = 7.2921151467e-5  # Earth's rotation rate (rad/s)
    
    # Check for NaN values in key parameters
    required_params = ['sqrt_A', 'e', 'M0', 'omega', 'OMEGA', 'i0', 'Delta_n', 'Cuc', 'Cus', 'Crc', 'Crs', 'Cic', 'Cis', 'IDOT', 'OMEGA_DOT']
    for param in required_params:
        if param not in closest_row or pd.isna(closest_row[param]):
            raise ValueError(f"Missing or NaN value for {param} in navigation data")
    
    # Semi-major axis
    A = closest_row['sqrt_A'] ** 2
    
    # Computed mean motion
    n0 = np.sqrt(mu / (A**3))
    
    # Time difference from epoch
    toe = closest_row['Toe']
    if isinstance(toe, float):
        # Toe is in seconds of GPS week
        # Try to get the GPS week - different satellite systems might use different column names
        week = None
        for week_col in ['GPS_week', 'GAL_week', 'BDT_week']:
            if week_col in closest_row and not pd.isna(closest_row[week_col]):
                try:
                    # Ensure the week is an integer
                    week = int(float(closest_row[week_col]))
                    break
                except (ValueError, TypeError):
                    # Skip if value can't be converted to int
                    continue
                
        if week is None:
            # If no week column is found, use current week as fallback
            # This is not accurate but better than failing completely
            current_week, _ = datetime_to_gps_time(datetime.now())
            week = current_week
            
        toe_datetime = gps_time_to_datetime(week, toe)
    else:
        # Toe is already a datetime
        toe_datetime = toe
    
    dt = (time - toe_datetime).total_seconds()
    
    # Corrected mean motion
    n = n0 + closest_row['Delta_n']
    
    # Mean anomaly at time t
    M = closest_row['M0'] + n * dt
    
    # Eccentric anomaly (iterative solution)
    e = closest_row['e']
    E = M
    for _ in range(10):  # Usually converges within a few iterations
        E_next = M + e * np.sin(E)
        if abs(E_next - E) < 1e-12:
            break
        E = E_next
    
    # True anomaly
    v = np.arctan2(np.sqrt(1 - e**2) * np.sin(E), np.cos(E) - e)
    
    # Argument of latitude
    phi = v + closest_row['omega']
    
    # Second harmonic perturbations
    du = closest_row['Cuc'] * np.cos(2*phi) + closest_row['Cus'] * np.sin(2*phi)  # Argument of latitude correction
    dr = closest_row['Crc'] * np.cos(2*phi) + closest_row['Crs'] * np.sin(2*phi)  # Radius correction
    di = closest_row['Cic'] * np.cos(2*phi) + closest_row['Cis'] * np.sin(2*phi)
    
    # Corrected argument of latitude
    u = phi + du
    
    # Corrected radius
    r = A * (1 - e * np.cos(E)) + dr
    
    # Corrected inclination
    i = closest_row['i0'] + di + closest_row['IDOT'] * dt
    
    # Positions in orbital plane
    x_prime = r * np.cos(u)
    y_prime = r * np.sin(u)
    
    # Corrected longitude of ascending node
    Omega = closest_row['OMEGA'] + (closest_row['OMEGA_DOT'] - omega_e) * dt - omega_e * toe
    
    # Earth-fixed coordinates
    X = x_prime * np.cos(Omega) - y_prime * np.cos(i) * np.sin(Omega)
    Y = x_prime * np.sin(Omega) + y_prime * np.cos(i) * np.cos(Omega)
    Z = y_prime * np.sin(i)
    
    # Velocity calculations (simplified)
    # Time derivative of eccentric anomaly
    E_dot = n / (1 - e * np.cos(E))
    
    # Time derivative of argument of latitude
    phi_dot = np.sqrt(1 - e**2) * E_dot / (1 - e * np.cos(E))
    
    # Time derivative of corrected argument of latitude
    u_dot = phi_dot * (1 + 2 * (closest_row['Cus'] * np.cos(2*phi) - closest_row['Cuc'] * np.sin(2*phi)))
    
    # Time derivative of corrected radius
    r_dot = A * e * np.sin(E) * E_dot + 2 * phi_dot * (closest_row['Crs'] * np.cos(2*phi) - closest_row['Crc'] * np.sin(2*phi))
    
    # Time derivatives in orbital plane
    x_prime_dot = r_dot * np.cos(u) - r * u_dot * np.sin(u)
    y_prime_dot = r_dot * np.sin(u) + r * u_dot * np.cos(u)
    
    # Time derivative of longitude of ascending node
    Omega_dot = closest_row['OMEGA_DOT'] - omega_e
    
    # Time derivative of corrected inclination
    i_dot = closest_row['IDOT'] + 2 * phi_dot * (closest_row['Cis'] * np.cos(2*phi) - closest_row['Cic'] * np.sin(2*phi))
    
    # Earth-fixed velocity components
    VX = (x_prime_dot * np.cos(Omega) - y_prime_dot * np.cos(i) * np.sin(Omega) - 
          y_prime * np.sin(i) * i_dot * np.sin(Omega) - 
          (x_prime * np.sin(Omega) + y_prime * np.cos(i) * np.cos(Omega)) * Omega_dot)
    
    VY = (x_prime_dot * np.sin(Omega) + y_prime_dot * np.cos(i) * np.cos(Omega) +
          y_prime * np.sin(i) * i_dot * np.cos(Omega) + 
          (x_prime * np.cos(Omega) - y_prime * np.cos(i) * np.sin(Omega)) * Omega_dot)
    
    VZ = y_prime_dot * np.sin(i) + y_prime * np.cos(i) * i_dot
    
    return {
        'X': X,
        'Y': Y,
        'Z': Z,
        'VX': VX,
        'VY': VY,
        'VZ': VZ
    }

def compute_sv_clock_correction(nav_data: pd.DataFrame, time: datetime, 
                               sat_system: str = 'G', prn: int = 1) -> float:
    """
    Compute satellite clock correction at a given time.
    
    Parameters
    ----------
    nav_data : pd.DataFrame
        Navigation data DataFrame for a specific satellite system.
    time : datetime
        Time at which to compute the clock correction.
    sat_system : str, optional
        Satellite system identifier (default: 'G' for GPS).
    prn : int, optional
        Satellite PRN number (default: 1).
        
    Returns
    -------
    float
        Clock correction value in seconds.
    """
    # Filter navigation data for the specific satellite
    sat_data = nav_data[nav_data['PRN'] == prn].sort_values('Epoch')
    
    if sat_data.empty:
        raise ValueError(f"No navigation data found for {sat_system}{prn:02d}")
    
    # Find the closest epoch before the requested time
    closest_row = sat_data[sat_data['Epoch'] <= time].iloc[-1]
    
    # Check for NaN values in key parameters
    required_params = ['SV_clock_bias', 'SV_clock_drift', 'SV_clock_drift_rate']
    for param in required_params:
        if param not in closest_row or pd.isna(closest_row[param]):
            raise ValueError(f"Missing or NaN value for {param} in navigation data")
    
    # Get clock parameters
    a0 = closest_row['SV_clock_bias']
    a1 = closest_row['SV_clock_drift']
    a2 = closest_row['SV_clock_drift_rate']
    
    # Time difference from epoch
    toc = closest_row['Epoch']  # Time of clock parameters
    dt = (time - toc).total_seconds()
    
    # Compute clock correction
    dt_corr = a0 + a1 * dt + a2 * dt**2
    
    # For GPS satellites, apply relativistic correction
    if sat_system in ['G', 'J']:
        # Check if we have the required orbital parameters
        if 'e' in closest_row and 'sqrt_A' in closest_row and not pd.isna(closest_row['e']) and not pd.isna(closest_row['sqrt_A']):
            # Get orbital parameters
            e = closest_row['e']
            A = closest_row['sqrt_A']**2
            
            # Compute eccentric anomaly for relativistic correction
            # (Simplified approach - for full implementation, use the same E as in interpolate_orbit)
            mu = 3.986005e14  # Earth's gravitational constant
            n0 = np.sqrt(mu / (A**3))
            
            if 'Toe' in closest_row and not pd.isna(closest_row['Toe']) and 'M0' in closest_row and not pd.isna(closest_row['M0']):
                toe = closest_row['Toe']
                if isinstance(toe, float):
                    # Toe is in seconds of GPS week
                    # Try to get the GPS week - different satellite systems might use different column names
                    week = None
                    for week_col in ['GPS_week', 'GAL_week', 'BDT_week']:
                        if week_col in closest_row and not pd.isna(closest_row[week_col]):
                            try:
                                # Ensure the week is an integer
                                week = int(float(closest_row[week_col]))
                                break
                            except (ValueError, TypeError):
                                # Skip if value can't be converted to int
                                continue
                        
                    if week is None:
                        # If no week column is found, use current week as fallback
                        # This is not accurate but better than failing completely
                        current_week, _ = datetime_to_gps_time(datetime.now())
                        week = current_week
                        
                    toe_datetime = gps_time_to_datetime(week, toe)
                else:
                    # Toe is already a datetime
                    toe_datetime = toe
                
                dt_toe = (time - toe_datetime).total_seconds()
                M = closest_row['M0'] + n0 * dt_toe
                
                # Iterative solution for eccentric anomaly
                E = M
                for _ in range(10):
                    E_next = M + e * np.sin(E)
                    if abs(E_next - E) < 1e-12:
                        break
                    E = E_next
                
                # Relativistic correction
                F = -2 * np.sqrt(mu) / (3e8**2)
                rel_corr = F * e * np.sqrt(A) * np.sin(E)
                
                # Add relativistic correction to the clock correction
                dt_corr += rel_corr
    
    return dt_corr

def detect_rinex_version(filename: str) -> float:
    """
    Detect the RINEX version from a navigation file.
    
    Parameters
    ----------
    filename : str
        Path to the RINEX navigation file.
        
    Returns
    -------
    float
        RINEX version number.
        
    Raises
    ------
    ValueError
        If the RINEX version cannot be determined.
    """
    with open(filename, 'r') as f:
        first_line = f.readline()
    
    try:
        version = float(first_line[:9].strip())
        return version
    except ValueError:
        raise ValueError(f"Cannot determine RINEX version from file: {filename}")