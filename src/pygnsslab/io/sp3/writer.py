"""
SP3 file writer module.

This module provides functionality to write SP3 format files,
supporting both SP3-c and SP3-d formats.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

from .metadata import SP3Epoch, SP3Header, SP3SatelliteRecord
from .utils import compute_mjd, gps_time_from_datetime


class SP3Writer:
    """
    Writer for SP3 (Standard Product 3) precise orbit files.
    
    This class can write both SP3-c and SP3-d format files.
    """
    
    def __init__(self, header: SP3Header, epochs: List[SP3Epoch]):
        """
        Initialize the SP3 writer.
        
        Parameters
        ----------
        header : SP3Header
            Header information for the SP3 file.
        epochs : List[SP3Epoch]
            List of epochs with satellite data.
        """
        self.header = header
        self.epochs = epochs
    
    def write(self, file_path: Union[str, Path]):
        """
        Write SP3 data to a file.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the output file.
        """
        with open(file_path, 'w') as file:
            self._write_header(file)
            self._write_epochs(file)
            file.write("**EOF **\n")
    
    def _write_header(self, file: TextIO):
        """
        Write the SP3 header to the file.
        
        Parameters
        ----------
        file : TextIO
            Open file handle for writing.
        """
        h = self.header
        dt = h.time
        
        # First line
        file.write(f"#{h.version}{h.file_type}{dt.year:4d} {dt.month:2d} {dt.day:2d} "
                   f"{dt.hour:2d} {dt.minute:2d} {dt.second:11.8f} "
                   f"{h.epoch_count:6d} {h.data_used:5s}{h.coordinate_system:5s}"
                   f"{h.orbit_type:3s} {h.agency:4s}{h.num_satellites:2d}\n")
        
        # Second line - if GPS week/SOW not provided, calculate them
        if h.gps_week == 0 and h.seconds_of_week == 0:
            gps_week, sow = gps_time_from_datetime(dt)
        else:
            gps_week, sow = h.gps_week, h.seconds_of_week
        
        # If MJD not provided, calculate it
        if h.mjd == 0 and h.fractional_day == 0:
            mjd, frac = compute_mjd(dt)
        else:
            mjd, frac = h.mjd, h.fractional_day
        
        file.write(f"##{gps_week:4d} {sow:15.8f} {h.epoch_interval:14.8f}"
                   f"{mjd:5d}{frac:15.13f}\n")
        
        # Satellite IDs
        for i in range(0, len(h.satellite_ids), 17):
            sat_block = h.satellite_ids[i:i+17]
            line = "+"
            for sat in sat_block:
                line += f" {sat:3s}"
            line += " " * (3 * (17 - len(sat_block)) + 1)  # Pad to fixed width
            file.write(f"{line}\n")
        
        # Satellite accuracy
        for i in range(0, len(h.satellite_ids), 17):
            sat_block = h.satellite_ids[i:i+17]
            line = "++"
            for sat in sat_block:
                acc = h.satellite_accuracy.get(sat, 0)
                line += f" {acc:2d}"
            line += " " * (3 * (17 - len(sat_block)) + 1)  # Pad to fixed width
            file.write(f"{line}\n")
        
        # File and time system
        file.write(f"%c {h.file_system} cc{h.time_system}ccc cccc cccc cccc cccc "
                   f"ccccc ccccc ccccc ccccc\n")
        
        # Additional fixed format lines for the header
        file.write("%c cccc cccc cccc cccc ccccc ccccc ccccc ccccc\n")
        file.write("%f 1.2500000 1.025000000 0.00000000000 0.000000000000000\n")
        file.write("%f 0.0000000 0.000000000 0.00000000000 0.000000000000000\n")
        file.write("%i 0 0 0 0 0 0 0 0 0\n")
        file.write("%i 0 0 0 0 0 0 0 0 0\n")
        
        # Write comments
        for comment in h.comments:
            file.write(f"/* {comment}\n")
        
        # End of header marker
        file.write("*\n")
    
    def _write_epochs(self, file: TextIO):
        """
        Write epoch data to the file.
        
        Parameters
        ----------
        file : TextIO
            Open file handle for writing.
        """
        for epoch in self.epochs:
            dt = epoch.time
            
            # Write epoch line
            file.write(f"*  {dt.year:4d} {dt.month:2d} {dt.day:2d} "
                       f"{dt.hour:2d} {dt.minute:2d} {dt.second:11.8f}\n")
            
            # Write satellite positions
            for sat_id, sat in sorted(epoch.satellites.items()):
                self._write_satellite_record(file, sat)
    
    def _write_satellite_record(self, file: TextIO, sat: SP3SatelliteRecord):
        """
        Write a satellite record to the file.
        
        Parameters
        ----------
        file : TextIO
            Open file handle for writing.
        sat : SP3SatelliteRecord
            The satellite record to write.
        """
        # Position record
        line = f"P{sat.sat_id:3s} {sat.x:14.6f} {sat.y:14.6f} {sat.z:14.6f} {sat.clock:14.6f}"
        
        # Add event flags if present
        if sat.event_flag is not None:
            line += f" {sat.event_flag:1d}"
            if sat.clock_event_flag is not None:
                line += f" {sat.clock_event_flag:1d}"
        
        file.write(f"{line}\n")
        
        # Position standard deviations if available
        if sat.x_sdev is not None and sat.y_sdev is not None and sat.z_sdev is not None and sat.clock_sdev is not None:
            file.write(f"EP{sat.sat_id:3s} {sat.x_sdev:5.0f} {sat.y_sdev:5.0f} "
                       f"{sat.z_sdev:5.0f} {sat.clock_sdev:5.0f}\n")
        
        # Velocity record if available and if file type is 'V'
        if self.header.file_type == 'V' and sat.x_vel is not None and sat.y_vel is not None and sat.z_vel is not None:
            file.write(f"V{sat.sat_id:3s} {sat.x_vel:14.6f} {sat.y_vel:14.6f} "
                       f"{sat.z_vel:14.6f} {sat.clock_rate or 0.0:14.6f}\n")
            
            # Velocity standard deviations if available
            if (sat.x_vel_sdev is not None and sat.y_vel_sdev is not None 
                    and sat.z_vel_sdev is not None and sat.clock_rate_sdev is not None):
                file.write(f"EV{sat.sat_id:3s} {sat.x_vel_sdev:5.0f} {sat.y_vel_sdev:5.0f} "
                          f"{sat.z_vel_sdev:5.0f} {sat.clock_rate_sdev:5.0f}\n")


def write_sp3_file(file_path: Union[str, Path], header: SP3Header, epochs: List[SP3Epoch]):
    """
    Write SP3 data to a file.
    
    Parameters
    ----------
    file_path : Union[str, Path]
        Path to the output file.
    header : SP3Header
        Header information for the SP3 file.
    epochs : List[SP3Epoch]
        List of epochs with satellite data.
    """
    writer = SP3Writer(header, epochs)
    writer.write(file_path)