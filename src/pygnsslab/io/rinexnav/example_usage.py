"""
Example usage of the RINEX Navigation reader module.

This script demonstrates how to use the RINEX Navigation reader to read navigation data
from files of different RINEX versions and how to process the data.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from pygnsslab.io.rinexnav.reader import read_rinex_nav
from pygnsslab.io.rinexnav.utils import (
    gps_time_to_datetime,
    datetime_to_gps_time,
    interpolate_orbit,
    compute_sv_clock_correction
)

def read_and_display_rinex2_nav(filename):
    """
    Read a RINEX 2 navigation file and display basic information.
    
    Parameters
    ----------
    filename : str
        Path to the RINEX 2 navigation file.
    """
    print(f"\nReading RINEX 2 Navigation file: {filename}")
    
    # Read the file
    nav_reader = read_rinex_nav(filename)
    
    # Display header information
    print("\nHeader Information:")
    for key, value in nav_reader.header.items():
        print(f"  {key}: {value}")
    
    # Display data summary
    print("\nData Summary:")
    for sys, df in nav_reader.data.items():
        if not df.empty:
            print(f"  System {sys}: {len(df)} records")
            print(f"  PRNs: {sorted(df['PRN'].unique())}")
            
            # Display time span
            min_time = df['Epoch'].min()
            max_time = df['Epoch'].max()
            print(f"  Time span: {min_time} to {max_time}")
            
            # Display first record
            print("\nFirst record:")
            display_record(df.iloc[0])

def read_and_display_rinex3_nav(filename):
    """
    Read a RINEX 3 navigation file and display basic information.
    
    Parameters
    ----------
    filename : str
        Path to the RINEX 3 navigation file.
    """
    print(f"\nReading RINEX 3 Navigation file: {filename}")
    
    # Read the file
    nav_reader = read_rinex_nav(filename)
    
    # Display header information
    print("\nHeader Information:")
    for key, value in nav_reader.header.items():
        if key not in ['ionospheric_corr', 'time_system_corr']:
            print(f"  {key}: {value}")
    
    # Display ionospheric correction if available
    if 'ionospheric_corr' in nav_reader.header:
        print("\nIonospheric Correction:")
        for corr_type, values in nav_reader.header['ionospheric_corr'].items():
            print(f"  {corr_type}: {values}")
    
    # Display time system correction if available
    if 'time_system_corr' in nav_reader.header:
        print("\nTime System Correction:")
        for corr_type, values in nav_reader.header['time_system_corr'].items():
            print(f"  {corr_type}: {values}")
    
    # Display data summary
    print("\nData Summary:")
    for sys, df in nav_reader.data.items():
        if not df.empty:
            print(f"\nSystem {sys}: {len(df)} records")
            print(f"  PRNs: {sorted(df['PRN'].unique())}")
            
            # Display time span
            min_time = df['Epoch'].min()
            max_time = df['Epoch'].max()
            print(f"  Time span: {min_time} to {max_time}")
            
            # Display first record
            print("\nFirst record for system", sys)
            display_record(df.iloc[0])

def display_record(record):
    """
    Display a navigation record in a readable format.
    
    Parameters
    ----------
    record : pd.Series
        Navigation record as a pandas Series.
    """
    # Display basic information
    print(f"  PRN: {record['PRN']}")
    print(f"  Epoch: {record['Epoch']}")
    print(f"  SV Clock Bias: {record['SV_clock_bias']:.12e} s")
    print(f"  SV Clock Drift: {record['SV_clock_drift']:.12e} s/s")
    print(f"  SV Clock Drift Rate: {record['SV_clock_drift_rate']:.12e} s/s²")
    
    # Display orbital parameters if they exist
    for param in ['IODE', 'e', 'sqrt_A', 'Toe']:
        if param in record and not pd.isna(record[param]):
            if param == 'sqrt_A':
                print(f"  {param}: {record[param]:.12e} m^(1/2)")
            elif param == 'e':
                print(f"  {param}: {record[param]:.12e} (dimensionless)")
            elif param == 'Toe':
                print(f"  {param}: {record[param]}")
            else:
                print(f"  {param}: {record[param]}")

def plot_satellite_orbit(nav_data, sat_system, prn, start_time, duration_hours):
    """
    Plot the satellite orbit over a specified time period.
    
    Parameters
    ----------
    nav_data : dict of pd.DataFrame
        Navigation data dictionary where keys are satellite systems.
    sat_system : str
        Satellite system identifier (e.g., 'G' for GPS).
    prn : int
        Satellite PRN number.
    start_time : datetime
        Start time for the plot.
    duration_hours : float
        Duration of the plot in hours.
    """
    if sat_system not in nav_data:
        print(f"No data available for satellite system {sat_system}")
        return
    
    # Get dataframe for the specified satellite system
    df = nav_data[sat_system]
    
    # Ensure the data contains the specified PRN
    if prn not in df['PRN'].values:
        print(f"No data available for satellite {sat_system}{prn}")
        return
    
    # Check if satellite system is supported for interpolation
    supported_systems = ['G']  # Currently only GPS is supported
    if sat_system not in supported_systems:
        print(f"Interpolation for satellite system {sat_system} is not supported yet. Skipping orbit plotting.")
        return
    
    # Create time points for interpolation
    num_points = int(duration_hours * 12)  # One point every 5 minutes
    times = [start_time + timedelta(hours=duration_hours*i/num_points) for i in range(num_points+1)]
    
    # Interpolate the orbit at each time point
    positions = []
    for t in times:
        try:
            pos = interpolate_orbit(df, t, sat_system, prn)
            # Check for NaN values in the position
            if np.isnan(pos['X']) or np.isnan(pos['Y']) or np.isnan(pos['Z']):
                continue
            positions.append((t, pos['X'], pos['Y'], pos['Z']))
        except Exception as e:
            print(f"Error interpolating at time {t}: {e}")
    
    # Extract coordinates for plotting
    if positions:
        t_vals, x_vals, y_vals, z_vals = zip(*positions)
        
        # Create the plot
        plt.figure(figsize=(12, 10))
        
        # 3D plot
        ax = plt.subplot(111, projection='3d')
        ax.plot(x_vals, y_vals, z_vals, 'b-', linewidth=2)
        
        # Plot Earth (simplified as a sphere)
        u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
        earth_radius = 6371000  # Earth's radius in meters
        x = earth_radius * np.cos(u) * np.sin(v)
        y = earth_radius * np.sin(u) * np.sin(v)
        z = earth_radius * np.cos(v)
        ax.plot_surface(x, y, z, color='g', alpha=0.2)
        
        # Add starting point marker
        ax.scatter([x_vals[0]], [y_vals[0]], [z_vals[0]], color='r', s=100, label='Start')
        
        # Set labels and title
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title(f'Orbit of Satellite {sat_system}{prn} over {duration_hours} hours')
        
        # Set equal aspect ratio
        max_range = max([max(x_vals) - min(x_vals), max(y_vals) - min(y_vals), max(z_vals) - min(z_vals)])
        mid_x = (max(x_vals) + min(x_vals)) * 0.5
        mid_y = (max(y_vals) + min(y_vals)) * 0.5
        mid_z = (max(z_vals) + min(z_vals)) * 0.5
        ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
        ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
        ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
        
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'satellite_{sat_system}{prn}_orbit.png', dpi=300)
        plt.close()
        
        print(f"Orbit plot saved as 'satellite_{sat_system}{prn}_orbit.png'")
        
        # Plot clock correction
        plt.figure(figsize=(10, 6))
        
        clock_corrections = []
        for t in times:
            try:
                clock_corr = compute_sv_clock_correction(df, t, sat_system, prn)
                clock_corrections.append(clock_corr)
            except Exception as e:
                print(f"Error computing clock correction at time {t}: {e}")
                clock_corrections.append(np.nan)
        
        # Remove NaN values for plotting
        valid_times = []
        valid_corrections = []
        for i, corr in enumerate(clock_corrections):
            if not np.isnan(corr):
                valid_times.append(times[i])
                valid_corrections.append(corr)
        
        if valid_corrections:
            # Convert to nanoseconds for better visualization
            clock_corrections_ns = [c * 1e9 for c in valid_corrections]
            
            # Create time axis in hours from start
            time_hours = [(t - start_time).total_seconds()/3600 for t in valid_times]
            
            plt.plot(time_hours, clock_corrections_ns, 'b-', linewidth=2)
            plt.xlabel('Time (hours from start)')
            plt.ylabel('Clock Correction (ns)')
            plt.title(f'Clock Correction of Satellite {sat_system}{prn} over {duration_hours} hours')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f'satellite_{sat_system}{prn}_clock_correction.png', dpi=300)
            plt.close()
            
            print(f"Clock correction plot saved as 'satellite_{sat_system}{prn}_clock_correction.png'")
        else:
            print("No valid clock corrections calculated for the specified time range.")
    else:
        print("No valid positions calculated for the specified time range.")

def compute_dop_values(nav_data, receiver_pos, time, visible_sats=None):
    """
    Compute Dilution of Precision (DOP) values.
    
    Parameters
    ----------
    nav_data : dict of pd.DataFrame
        Navigation data dictionary where keys are satellite systems.
    receiver_pos : tuple of float
        Receiver position (X, Y, Z) in ECEF coordinates.
    time : datetime
        Time for DOP computation.
    visible_sats : list of tuple, optional
        List of visible satellites as (system, prn) tuples.
        If None, all satellites in the navigation data are used.
        
    Returns
    -------
    dict
        Dictionary containing DOP values (GDOP, PDOP, HDOP, VDOP, TDOP).
    """
    # Currently supported satellite systems for interpolation
    supported_systems = ['G']  # Currently only GPS is supported
    
    if visible_sats is None:
        # Use all satellites in the navigation data from supported systems
        visible_sats = []
        for sys, df in nav_data.items():
            if sys in supported_systems:
                for prn in df['PRN'].unique():
                    visible_sats.append((sys, prn))
        
        if not visible_sats:
            print(f"No satellites from supported systems ({', '.join(supported_systems)}) found in navigation data.")
            return None
    
    # Compute satellite positions
    sat_positions = []
    
    for sys, prn in visible_sats:
        if sys not in supported_systems:
            continue  # Skip unsupported satellite systems
            
        if sys in nav_data and prn in nav_data[sys]['PRN'].values:
            try:
                pos = interpolate_orbit(nav_data[sys], time, sys, prn)
                # Check for NaN values in the position
                if np.isnan(pos['X']) or np.isnan(pos['Y']) or np.isnan(pos['Z']):
                    continue
                sat_positions.append((sys, prn, pos['X'], pos['Y'], pos['Z']))
            except Exception as e:
                print(f"Error interpolating position for {sys}{prn} at {time}: {e}")
    
    if len(sat_positions) < 4:
        print(f"Insufficient satellites ({len(sat_positions)}) for DOP computation.")
        return None
    
    # Compute line-of-sight unit vectors
    rx, ry, rz = receiver_pos
    G_matrix = []
    
    for _, _, sx, sy, sz in sat_positions:
        # Vector from receiver to satellite
        dx = sx - rx
        dy = sy - ry
        dz = sz - rz
        
        # Range
        range_val = np.sqrt(dx**2 + dy**2 + dz**2)
        
        # Unit vector components
        ax = dx / range_val
        ay = dy / range_val
        az = dz / range_val
        
        # Add to G matrix with clock term
        G_matrix.append([ax, ay, az, 1])
    
    # Compute DOP from G matrix
    G = np.array(G_matrix)
    try:
        Q = np.linalg.inv(G.T @ G)
        
        # Extract DOP values
        GDOP = np.sqrt(np.trace(Q))
        PDOP = np.sqrt(Q[0,0] + Q[1,1] + Q[2,2])
        HDOP = np.sqrt(Q[0,0] + Q[1,1])
        VDOP = np.sqrt(Q[2,2])
        TDOP = np.sqrt(Q[3,3])
        
        return {
            'GDOP': GDOP,
            'PDOP': PDOP,
            'HDOP': HDOP,
            'VDOP': VDOP,
            'TDOP': TDOP
        }
    except np.linalg.LinAlgError as e:
        print(f"Linear algebra error in DOP computation: {e}")
        return None

def verify_data_integrity(nav_data, sat_system):
    """
    Verify the integrity of navigation data by checking for required parameters.
    
    Parameters
    ----------
    nav_data : dict of pd.DataFrame
        Navigation data dictionary where keys are satellite systems.
    sat_system : str
        Satellite system identifier (e.g., 'G' for GPS).
        
    Returns
    -------
    list
        List of valid PRNs with complete data for orbit calculations.
    """
    if sat_system not in nav_data:
        print(f"No data available for satellite system {sat_system}")
        return []
    
    # Get dataframe for the specified satellite system
    df = nav_data[sat_system]
    
    # List of required parameters for orbit calculations
    required_params = ['sqrt_A', 'e', 'M0', 'omega', 'OMEGA', 'i0', 'Delta_n', 
                       'Cuc', 'Cus', 'Crc', 'Crs', 'Cic', 'Cis', 'IDOT', 'OMEGA_DOT', 'Toe']
    
    valid_prns = []
    
    # Check all unique PRNs in the dataframe
    for prn in df['PRN'].unique():
        # Get all records for this PRN
        prn_data = df[df['PRN'] == prn]
        
        # Check if there's at least one complete record
        for _, row in prn_data.iterrows():
            is_valid = True
            for param in required_params:
                if param not in row or pd.isna(row[param]):
                    is_valid = False
                    break
            
            if is_valid:
                valid_prns.append(prn)
                break
    
    return valid_prns

def main():
    """Main function to demonstrate the usage of the RINEX Navigation reader."""
    # Example usage with RINEX 2 file
    rinex2_file = "data/nav/ajac0010.22n"  # Replace with actual path
    
    try:
        # Read RINEX 2 navigation file
        nav_reader_v2 = read_rinex_nav(rinex2_file)
        read_and_display_rinex2_nav(rinex2_file)
        
        # Verify data integrity and find valid satellites
        if 'G' in nav_reader_v2.data:
            valid_prns = verify_data_integrity(nav_reader_v2.data, 'G')
            print(f"\nValid GPS satellites in RINEX 2 file with complete orbital data: {valid_prns}")
            
            if valid_prns:
                prn_to_plot = valid_prns[0]  # Choose the first valid PRN
                
                # Find a suitable start time (with valid data)
                # Use a time within the data range
                all_epochs = sorted(nav_reader_v2.data['G']['Epoch'].unique())
                if all_epochs:
                    # Choose a time that's not at the very beginning or end
                    start_idx = len(all_epochs) // 4  # 25% into the data
                    start_time = all_epochs[start_idx]
                    
                    print(f"\nPlotting orbit for GPS satellite PRN {prn_to_plot} starting at {start_time}")
                    plot_satellite_orbit(nav_reader_v2.data, 'G', prn_to_plot, start_time, 12)  # Reduced to 12 hours
                    
                    # Example of DOP computation
                    # Receiver position in ECEF coordinates (example: near Greenwich)
                    receiver_pos = (3980000, 0, 4970000)
                    print(f"\nComputing DOP values at {start_time}")
                    dop_values = compute_dop_values(nav_reader_v2.data, receiver_pos, start_time)
                    if dop_values:
                        print("\nDOP Values:")
                        for key, value in dop_values.items():
                            print(f"  {key}: {value:.2f}")
                    else:
                        print("Could not compute DOP values.")
                else:
                    print("No GPS epoch data available for plotting.")
            else:
                print("No GPS satellites with complete orbital data found in the RINEX 2 file.")
        else:
            print("No GPS data found in the RINEX 2 file.")
    
    except Exception as e:
        print(f"Error processing RINEX 2 file: {e}")
    
    # Example usage with RINEX 3 file
    rinex3_file = "data/nav/PTLD00AUS_R_20220010000_01D_30S_MN.rnx"  # Replace with actual path
    
    try:
        # Read RINEX 3 navigation file
        nav_reader_v3 = read_rinex_nav(rinex3_file)
        read_and_display_rinex3_nav(rinex3_file)
        
        # Verify data integrity and find valid satellites
        if 'G' in nav_reader_v3.data:
            valid_prns = verify_data_integrity(nav_reader_v3.data, 'G')
            print(f"\nValid GPS satellites in RINEX 3 file with complete orbital data: {valid_prns}")
            
            if valid_prns:
                prn_to_plot = valid_prns[0]  # Choose the first valid PRN
                
                # Find a suitable start time (with valid data)
                all_epochs = sorted(nav_reader_v3.data['G']['Epoch'].unique())
                if all_epochs:
                    # Choose a time that's not at the very beginning or end
                    start_idx = len(all_epochs) // 4  # 25% into the data
                    start_time = all_epochs[start_idx]
                    
                    print(f"\nPlotting orbit for GPS satellite PRN {prn_to_plot} from RINEX 3 file starting at {start_time}")
                    plot_satellite_orbit(nav_reader_v3.data, 'G', prn_to_plot, start_time, 12)  # Reduced to 12 hours
                else:
                    print("No GPS epoch data available for plotting from RINEX 3.")
            else:
                print("No GPS satellites with complete orbital data found in the RINEX 3 file.")
        else:
            print("No GPS data found in the RINEX 3 file.")
        
        # Print a note about unsupported satellite systems
        unsupported_systems = [sys for sys in nav_reader_v3.data.keys() if sys != 'G']
        if unsupported_systems:
            print(f"\nNote: Interpolation for satellite systems {', '.join(unsupported_systems)} is not yet supported.")
            print("Only GPS (G) satellites can be used for orbit plotting and DOP calculations.")
    
    except Exception as e:
        print(f"Error processing RINEX 3 file: {e}")

if __name__ == "__main__":
    main()