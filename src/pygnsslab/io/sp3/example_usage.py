"""
Example usage of the SP3 module.

This module demonstrates how to read, manipulate, and write SP3 files.
"""

from datetime import datetime, timedelta
import os
import sys
import matplotlib.pyplot as plt
import numpy as np

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pygnsslab.io.sp3.reader import SP3Reader
from pygnsslab.io.sp3.writer import write_sp3_file
from pygnsslab.io.sp3.metadata import SP3Header, SP3Epoch, SP3SatelliteRecord


def read_sp3_file(file_path):
    """
    Read an SP3 file and print basic information.
    
    Parameters
    ----------
    file_path : str
        Path to the SP3 file.
    """
    # Read the SP3 file
    print(f"Reading SP3 file: {file_path}")
    reader = SP3Reader(file_path)
    
    # Print header information
    header = reader.header
    print("\nHeader Information:")
    print(f"  Version: SP3-{header.version}")
    print(f"  File Type: {header.file_type}")
    print(f"  Time: {header.time}")
    print(f"  Epoch Count: {header.epoch_count}")
    print(f"  Satellite Count: {header.num_satellites}")
    if header.satellite_ids:
        satellite_ids_str = ', '.join(header.satellite_ids[:5])
        if len(header.satellite_ids) > 5:
            satellite_ids_str += "..."
        print(f"  Satellites: {satellite_ids_str}")
    else:
        print("  Satellites: None")
    
    # Print information about the first epoch
    if reader.epochs:
        first_epoch = reader.epochs[0]
        print("\nFirst Epoch Information:")
        print(f"  Time: {first_epoch.time}")
        print(f"  Number of Satellites: {len(first_epoch.satellites)}")
        
        # Print information about the first satellite in the first epoch
        if first_epoch.satellites:
            first_sat_id = list(first_epoch.satellites.keys())[0]
            first_sat = first_epoch.satellites[first_sat_id]
            print(f"\nSatellite {first_sat_id} Information:")
            print(f"  Position (X, Y, Z): ({first_sat.x}, {first_sat.y}, {first_sat.z}) km")
            print(f"  Clock: {first_sat.clock} µs")
            
            if first_sat.x_vel is not None:
                print(f"  Velocity (X, Y, Z): ({first_sat.x_vel}, {first_sat.y_vel}, {first_sat.z_vel}) dm/s")
    
    # Print summary
    print("\nSummary:")
    print(f"  Number of Epochs: {len(reader.epochs)}")
    if len(reader.epochs) > 1:
        time_diff = reader.epochs[1].time - reader.epochs[0].time
        print(f"  Epoch Interval: {time_diff.total_seconds()} seconds")
    
    return reader


def plot_satellite_positions(reader, satellite_id, title=None):
    """
    Plot the positions of a satellite over time.
    
    Parameters
    ----------
    reader : SP3Reader
        The SP3 reader object.
    satellite_id : str
        The satellite ID to plot.
    title : str, optional
        The title for the plot.
    """
    positions = reader.get_satellite_positions(satellite_id)
    if not positions:
        print(f"No position data for satellite {satellite_id}")
        return
    
    # Extract data for plotting
    times = [pos[0] for pos in positions]
    x_coords = [pos[1] for pos in positions]
    y_coords = [pos[2] for pos in positions]
    z_coords = [pos[3] for pos in positions]
    
    # Create a figure with 3 subplots
    fig, axs = plt.subplots(3, 1, figsize=(10, 12))
    
    # Convert datetime to hours from the first epoch for x-axis
    t0 = times[0]
    hours = [(t - t0).total_seconds() / 3600 for t in times]
    
    # Plot X coordinate
    axs[0].plot(hours, x_coords, 'r-')
    axs[0].set_ylabel('X Coordinate (km)')
    axs[0].set_title(f'Satellite {satellite_id} Position - X Coordinate')
    axs[0].grid(True)
    
    # Plot Y coordinate
    axs[1].plot(hours, y_coords, 'g-')
    axs[1].set_ylabel('Y Coordinate (km)')
    axs[1].set_title(f'Satellite {satellite_id} Position - Y Coordinate')
    axs[1].grid(True)
    
    # Plot Z coordinate
    axs[2].plot(hours, z_coords, 'b-')
    axs[2].set_xlabel('Time (hours from start)')
    axs[2].set_ylabel('Z Coordinate (km)')
    axs[2].set_title(f'Satellite {satellite_id} Position - Z Coordinate')
    axs[2].grid(True)
    
    # Add a main title if provided
    if title:
        fig.suptitle(title, fontsize=16)
    
    plt.tight_layout()
    plt.show(block=True)


def plot_satellite_3d_orbit(reader, satellite_id, title=None):
    """
    Create a 3D plot of the satellite orbit.
    
    Parameters
    ----------
    reader : SP3Reader
        The SP3 reader object.
    satellite_id : str
        The satellite ID to plot.
    title : str, optional
        The title for the plot.
    """
    positions = reader.get_satellite_positions(satellite_id)
    if not positions:
        print(f"No position data for satellite {satellite_id}")
        return
    
    # Extract data for plotting
    x_coords = [pos[1] for pos in positions]
    y_coords = [pos[2] for pos in positions]
    z_coords = [pos[3] for pos in positions]
    
    # Create a figure
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot orbit
    ax.plot(x_coords, y_coords, z_coords, 'b-', label=f'Satellite {satellite_id} Orbit')
    
    # Plot the Earth (simplified as a sphere)
    # Earth radius in km
    r_earth = 6371.0
    
    # Create a sphere
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x = r_earth * np.cos(u) * np.sin(v)
    y = r_earth * np.sin(u) * np.sin(v)
    z = r_earth * np.cos(v)
    
    # Plot Earth with low alpha for transparency
    ax.plot_surface(x, y, z, color='blue', alpha=0.1)
    
    # Set labels and title
    ax.set_xlabel('X (km)')
    ax.set_ylabel('Y (km)')
    ax.set_zlabel('Z (km)')
    
    if title:
        ax.set_title(title)
    else:
        ax.set_title(f'Satellite {satellite_id} Orbit')
    
    # Set axis limits to be equal for proper sphere rendering
    max_range = max(
        max(x_coords) - min(x_coords),
        max(y_coords) - min(y_coords),
        max(z_coords) - min(z_coords)
    ) / 2.0
    
    mid_x = (max(x_coords) + min(x_coords)) / 2
    mid_y = (max(y_coords) + min(y_coords)) / 2
    mid_z = (max(z_coords) + min(z_coords)) / 2
    
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)
    
    plt.tight_layout()
    plt.show()


def create_sample_sp3_file(output_file_path):
    """
    Create a sample SP3 file with some test data.
    
    Parameters
    ----------
    output_file_path : str
        Path to the output SP3 file.
    """
    # Create header
    header = SP3Header(
        version='c',  # SP3-c format
        file_type='P',  # Position only
        time=datetime(2023, 1, 1, 0, 0, 0),
        epoch_count=24,  # 24 epochs
        data_used="ORBIT",
        coordinate_system="IGS14",
        orbit_type="FIT",
        agency="TEST",
        gps_week=2245,
        seconds_of_week=0.0,
        epoch_interval=3600.0,  # 1 hour
        mjd=59945,
        fractional_day=0.0,
        num_satellites=3,
        satellite_ids=["G01", "G02", "G03"],
        satellite_accuracy={"G01": 7, "G02": 6, "G03": 7},
        file_system="G",
        time_system="GPS",
        comments=["This is a sample SP3 file", "Created for demonstration purposes"]
    )
    
    # Create epochs with satellite data
    epochs = []
    for i in range(24):  # 24 hours
        epoch_time = header.time + timedelta(hours=i)
        epoch = SP3Epoch(time=epoch_time)
        
        # Angular position around Earth (simplified circular orbit)
        angle_g01 = 2 * np.pi * i / 12  # 12-hour orbit for G01
        angle_g02 = 2 * np.pi * i / 11  # 11-hour orbit for G02
        angle_g03 = 2 * np.pi * i / 10  # 10-hour orbit for G03
        
        # Orbital radius in km (simplified)
        radius_g01 = 26000.0
        radius_g02 = 26500.0
        radius_g03 = 27000.0
        
        # Satellite positions in Earth-centered coordinates
        # G01
        x_g01 = radius_g01 * np.cos(angle_g01)
        y_g01 = radius_g01 * np.sin(angle_g01)
        z_g01 = 5000.0 * np.sin(angle_g01 * 2)  # Add some Z variation
        
        # G02
        x_g02 = radius_g02 * np.cos(angle_g02)
        y_g02 = radius_g02 * np.sin(angle_g02)
        z_g02 = 5500.0 * np.sin(angle_g02 * 2)  # Add some Z variation
        
        # G03
        x_g03 = radius_g03 * np.cos(angle_g03)
        y_g03 = radius_g03 * np.sin(angle_g03)
        z_g03 = 6000.0 * np.sin(angle_g03 * 2)  # Add some Z variation
        
        # Add satellite records to the epoch
        epoch.satellites["G01"] = SP3SatelliteRecord(
            sat_id="G01",
            x=x_g01,
            y=y_g01,
            z=z_g01,
            clock=100.0 + i * 0.1,  # Simulated clock bias
            x_sdev=5.0,
            y_sdev=5.0,
            z_sdev=5.0,
            clock_sdev=10.0
        )
        
        epoch.satellites["G02"] = SP3SatelliteRecord(
            sat_id="G02",
            x=x_g02,
            y=y_g02,
            z=z_g02,
            clock=200.0 + i * 0.2,  # Simulated clock bias
            x_sdev=5.0,
            y_sdev=5.0,
            z_sdev=5.0,
            clock_sdev=10.0
        )
        
        epoch.satellites["G03"] = SP3SatelliteRecord(
            sat_id="G03",
            x=x_g03,
            y=y_g03,
            z=z_g03,
            clock=300.0 + i * 0.3,  # Simulated clock bias
            x_sdev=5.0,
            y_sdev=5.0,
            z_sdev=5.0,
            clock_sdev=10.0
        )
        
        epochs.append(epoch)
    
    # Write the SP3 file
    write_sp3_file(output_file_path, header, epochs)
    print(f"Created sample SP3 file: {output_file_path}")


def main(show_plots=False):
    """
    Main function to demonstrate the SP3 module functionality.
    
    Parameters
    ----------
    show_plots : bool, optional
        Whether to show the plots, by default False
    """
    # Set the path to the example SP3 file
    # You should replace this with the path to your actual SP3 file
    sp3_file_path = "data/sp3/COD0MGXFIN_20220010000_01D_05M_ORB.SP3"
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(sp3_file_path), exist_ok=True)
    
    # Create a sample SP3 file
    create_sample_sp3_file(sp3_file_path)
    
    # Read the SP3 file
    reader = read_sp3_file(sp3_file_path)
    
    # Plot satellite positions and orbits if requested
    if show_plots:
        # Plot satellite positions
        plot_satellite_positions(reader, "G01", "Satellite G01 Position Over Time")
        
        # Plot satellite 3D orbit
        plot_satellite_3d_orbit(reader, "G01", "Satellite G01 Orbit")


if __name__ == "__main__":
    # Set show_plots to False to avoid blocking when running as a module
    main(show_plots=False)