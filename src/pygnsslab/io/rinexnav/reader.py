"""
RINEX Navigation File Reader.

This module provides classes and functions to read RINEX Navigation files
of versions 2, 3, and 4 and convert them to pandas DataFrames.
"""

import os
import re
import numpy as np
import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Union, Any

class RinexNavReader(ABC):
    """
    Abstract base class for RINEX navigation file readers.
    """
    def __init__(self, filename: str):
        """
        Initialize RINEX Navigation reader.
        
        Parameters
        ----------
        filename : str
            Path to the RINEX navigation file.
        """
        self.filename = filename
        self.version = None
        self.file_type = None
        self.header = {}
        self.data = {}
        self._read_file()
    
    def _read_file(self) -> None:
        """Read and parse the RINEX navigation file."""
        with open(self.filename, 'r') as f:
            content = f.read()
        
        # Split into header and data sections
        header_end_pattern = re.compile(r".*END OF HEADER.*\n", re.IGNORECASE)
        match = header_end_pattern.search(content)
        
        if match:
            header_content = content[:match.end()]
            data_content = content[match.end():]
            
            # Parse header and data
            self._parse_header(header_content)
            self._parse_data(data_content)
        else:
            raise ValueError("Invalid RINEX file: END OF HEADER marker not found")
    
    @abstractmethod
    def _parse_header(self, header_content: str) -> None:
        """Parse the header section of the RINEX file."""
        pass
    
    @abstractmethod
    def _parse_data(self, data_content: str) -> None:
        """Parse the data section of the RINEX file."""
        pass
    
    def to_dataframe(self) -> Dict[str, pd.DataFrame]:
        """
        Convert the navigation data to pandas DataFrames.
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary of DataFrames where keys are satellite system identifiers
            and values are the corresponding navigation data DataFrames.
        """
        return self.data


class Rinex2NavReader(RinexNavReader):
    """
    Reader for RINEX version 2.xx navigation files.
    """
    
    def _parse_header(self, header_content: str) -> None:
        """
        Parse the header section of a RINEX 2 navigation file.
        
        Parameters
        ----------
        header_content : str
            String containing the header section of the RINEX file.
        """
        lines = header_content.strip().split('\n')
        
        # Parse the first line for version and file type
        first_line = lines[0]
        self.version = float(first_line[:9].strip())
        
        # For RINEX 2 navigation files, the file type should be 'N'
        # Try multiple approaches to extract the file type
        if "N:" in first_line:
            # If we find 'N:' pattern, use 'N' as file type
            self.file_type = 'N'
        elif first_line[20:21].strip():
            # Try position 20 as fallback
            self.file_type = first_line[20:21].strip()
        else:
            # Default for navigation files
            self.file_type = 'N'
        
        self.header['version'] = self.version
        self.header['file_type'] = self.file_type
        
        # Parse the rest of the header
        for line in lines[1:]:
            label = line[60:].strip()
            
            if "PGM / RUN BY / DATE" in label:
                self.header['program'] = line[:20].strip()
                self.header['run_by'] = line[20:40].strip()
                self.header['created'] = line[40:60].strip()
            elif "COMMENT" in label:
                if 'comments' not in self.header:
                    self.header['comments'] = []
                self.header['comments'].append(line[:60].strip())
            # Add other header items as needed
            
    def _parse_data(self, data_content: str) -> None:
        """
        Parse the data section of a RINEX 2 Navigation file.
        
        Parameters
        ----------
        data_content : str
            String containing the data section of the RINEX file.
        """
        lines = data_content.strip().split('\n')
        records = []
        
        # Debug flag - set to False to disable debug output
        show_debug = False
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            if not line:
                i += 1
                continue
                
            # First line contains epoch and satellite info
            try:
                # Parse PRN and epoch from first line
                prn = int(line[:2].strip())
                year = int(line[3:5].strip())
                
                # For 2-digit years, follow the RINEX convention:
                # - If yy >= 80, assume 19yy
                # - If yy < 80, assume 20yy
                if year >= 80:
                    year += 1900
                else:
                    year += 2000
                    
                month = int(line[6:8].strip())
                day = int(line[9:11].strip())
                hour = int(line[12:14].strip())
                minute = int(line[15:17].strip())
                second = float(line[17:22].strip())
                
                # Parse SV clock terms directly from the header line
                # In RINEX 2, these are in columns 23-41, 42-60, 61-79
                sv_clock_bias = self._parse_rinex_float(line[22:41])
                sv_clock_drift = self._parse_rinex_float(line[41:60])
                sv_clock_drift_rate = self._parse_rinex_float(line[60:79])
                
                # Create epoch datetime
                epoch = datetime(year, month, day, hour, minute, int(second),
                              int((second - int(second)) * 1e6))
                
                # Initialize record with header values
                record = {
                    'PRN': prn,
                    'Epoch': epoch,
                    'Toc': epoch,
                    'SV_clock_bias': sv_clock_bias,
                    'SV_clock_drift': sv_clock_drift,
                    'SV_clock_drift_rate': sv_clock_drift_rate,
                }
                
                # Define parameter names according to GPS RINEX 2.11 specification
                param_names = [
                    'IODE', 'Crs', 'Delta_n', 'M0',                  # Line 1
                    'Cuc', 'e', 'Cus', 'sqrt_A',                     # Line 2
                    'Toe', 'Cic', 'OMEGA', 'Cis',                    # Line 3
                    'i0', 'Crc', 'omega', 'OMEGA_DOT',               # Line 4
                    'IDOT', 'L2_codes', 'GPS_week', 'L2_P_flag',     # Line 5
                    'SV_accuracy', 'SV_health', 'TGD', 'IODC',       # Line 6
                    'Transmission_time', 'Fit_interval'              # Line 7
                ]
                
                # In RINEX 2.11, each parameter field is exactly 19 characters wide
                # For the continuation lines, there's a 3-character space at the beginning
                # So parameters are at positions 4-22, 23-41, 42-60, 61-79
                orbital_params = {}
                
                # Process the next 7 lines for orbital parameters
                param_index = 0
                
                for j in range(1, 8):  # 7 lines of orbital parameters
                    if i + j >= len(lines):
                        break  # No more lines
                    
                    line = lines[i + j].rstrip()
                    if not line:
                        continue  # Skip empty lines
                    
                    # Process the 4 parameters on this line
                    # In RINEX 2.11, parameters are in fixed columns
                    for k in range(4):
                        if param_index >= len(param_names):
                            break  # We've processed all expected parameters
                        
                        param_name = param_names[param_index]
                        param_index += 1
                        
                        # Fixed column positions in RINEX 2.11 (0-indexed)
                        column_starts = [3, 22, 41, 60]
                        column_ends = [22, 41, 60, 79]
                        
                        # Ensure we're within bounds of the line
                        if column_starts[k] < len(line):
                            # Get the parameter field, ensuring we don't go out of bounds
                            end_pos = min(column_ends[k], len(line))
                            field = line[column_starts[k]:end_pos].strip()
                            
                            if field:  # Non-empty field
                                try:
                                    param_value = self._parse_rinex_float(field)
                                    orbital_params[param_name] = param_value
                                    
                                    if show_debug and param_index <= 4:  # Show first few for debugging
                                        print(f"Parsed {param_name}: {field} -> {param_value}")
                                except ValueError as e:
                                    orbital_params[param_name] = np.nan
                                    if show_debug and param_index <= 4:
                                        print(f"Error parsing {param_name}: {e} from '{field}'")
                            else:
                                orbital_params[param_name] = np.nan
                                if show_debug and param_index <= 4:
                                    print(f"Empty field for {param_name}")
                        else:
                            orbital_params[param_name] = np.nan
                            if show_debug and param_index <= 4:
                                print(f"Field out of range for {param_name}")
                
                # Update record with orbital parameters
                record.update(orbital_params)
                records.append(record)
                
                if show_debug and len(records) == 1:  # Show first record for debugging
                    print(f"\nFirst record orbital parameters:")
                    for name in param_names:
                        if name in record:
                            print(f"{name}: {record[name]}")
                
            except Exception as e:
                if show_debug:
                    print(f"Error processing record: {e}")
            
            # Move to the next record (8 lines per record)
            i += 8
        
        # Convert to DataFrame and store by constellation (default to GPS for RINEX 2)
        if records:
            self.data['G'] = pd.DataFrame(records)
        else:
            self.data['G'] = pd.DataFrame()

    def _parse_rinex_float(self, value_str: str) -> float:
        """
        Parse RINEX format floating point value, handling D-notation scientific format.
        
        RINEX uses 'D' instead of 'E' for exponents, like: 5.123456789D-01
        
        Parameters
        ----------
        value_str : str
            String containing the RINEX format value
            
        Returns
        -------
        float
            Parsed floating point value
        """
        # Handle empty input
        if not value_str or value_str.isspace():
            return 0.0
        
        # Clean up the input string
        value_str = value_str.strip()
        
        # Try direct conversion first (for simple cases without D notation)
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Most common case: D-notation scientific values
        # Format: 1.234567890D+01 or -1.234567890D-01
        if 'D' in value_str:
            # Handle standard RINEX D notation (D with +/- exponent)
            if 'D+' in value_str or 'D-' in value_str:
                # Simple replacement of D with E for Python's scientific notation
                try:
                    return float(value_str.replace('D', 'E'))
                except ValueError:
                    pass
            
            # Handle D notation with space after D before sign
            # Example: 1.234567890D +01 or 1.234567890D -01
            if 'D ' in value_str:
                try:
                    # Remove spaces after D and before sign
                    clean_value = value_str.replace('D ', 'D')
                    # Then replace D with E
                    clean_value = clean_value.replace('D', 'E')
                    return float(clean_value)
                except ValueError:
                    pass
                    
            # Handle the case where D and the exponent are separated
            # For example: "1.234567890D+01 something_else"
            try:
                parts = value_str.split('D')
                if len(parts) >= 2:
                    mantissa = float(parts[0])
                    
                    # Get just the exponent part (might have trailing text)
                    exponent_part = parts[1].strip()
                    
                    # Extract the exponent value with sign
                    import re
                    exponent_match = re.match(r'^([+-]?\d+)', exponent_part)
                    if exponent_match:
                        exponent = int(exponent_match.group(1))
                        return mantissa * (10 ** exponent)
            except (ValueError, IndexError):
                pass
        
        # Try other cleanup approaches for problematic cases
        # Remove all spaces and try again
        try:
            # Replace any D with E and remove all spaces
            clean_value = value_str.replace('D', 'E').replace(' ', '')
            return float(clean_value)
        except ValueError:
            pass
            
        # Last resort: extract the first valid float-like pattern using regex
        try:
            import re
            # Match a number with optional scientific notation
            matches = re.findall(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][-+]?\d+)?', value_str)
            if matches:
                # Use the first match and replace D with E
                return float(matches[0].replace('D', 'E'))
        except Exception:
            pass
            
        # If all attempts fail, return NaN
        return np.nan


class Rinex3NavReader(RinexNavReader):
    """
    Reader for RINEX version 3.xx and 4.xx navigation files.
    """
    
    def _parse_header(self, header_content: str) -> None:
        """
        Parse the header section of a RINEX 3 navigation file.
        
        Parameters
        ----------
        header_content : str
            String containing the header section of the RINEX file.
        """
        lines = header_content.strip().split('\n')
        
        # Parse the first line for version and file type
        first_line = lines[0]
        self.version = float(first_line[:9].strip())
        
        # For RINEX 3 navigation files, the file type should be 'N'
        # Try multiple approaches to extract the file type
        if "N:" in first_line:
            # If we find 'N:' pattern, use 'N' as file type
            self.file_type = 'N'
        elif first_line[20:21].strip():
            # Try position 20 as fallback
            self.file_type = first_line[20:21].strip()
        else:
            # Default for navigation files
            self.file_type = 'N'
        
        self.header['version'] = self.version
        self.header['file_type'] = self.file_type
        self.header['file_type_full'] = first_line[20:40].strip()  # Store full description as separate field
        
        # Parse the rest of the header
        for line in lines[1:]:
            label = line[60:].strip()
            
            if "PGM / RUN BY / DATE" in label:
                self.header['program'] = line[:20].strip()
                self.header['run_by'] = line[20:40].strip()
                self.header['created'] = line[40:60].strip()
            elif "COMMENT" in label:
                if 'comments' not in self.header:
                    self.header['comments'] = []
                self.header['comments'].append(line[:60].strip())
            elif "IONOSPHERIC CORR" in label:
                if 'ionospheric_corr' not in self.header:
                    self.header['ionospheric_corr'] = {}
                corr_type = line[:4].strip()
                
                # More robust parsing of ionospheric correction values
                corr_values = []
                for field_idx, slice_range in enumerate([(5, 14), (14, 23), (23, 32), (32, 41)]):
                    try:
                        value_str = line[slice_range[0]:slice_range[1]].strip().replace('D', 'E')
                        if value_str:
                            try:
                                value = float(value_str)
                            except ValueError:
                                # Handle potential formatting issues
                                if 'E' in value_str and not (value_str.endswith('E') or value_str.endswith('E-') or value_str.endswith('E+')):
                                    value = float(value_str)
                                else:
                                    value = 0.0  # Default value if parsing fails
                        else:
                            value = 0.0
                    except Exception:
                        value = 0.0
                    corr_values.append(value)
                
                self.header['ionospheric_corr'][corr_type] = corr_values
            elif "TIME SYSTEM CORR" in label:
                if 'time_system_corr' not in self.header:
                    self.header['time_system_corr'] = {}
                corr_type = line[:4].strip()
                
                # More robust parsing of time system correction values
                try:
                    a0_str = line[5:24].strip().replace('D', 'E')
                    a0 = float(a0_str) if a0_str else 0.0
                except ValueError:
                    a0 = 0.0
                    
                try:
                    a1_str = line[24:43].strip().replace('D', 'E')
                    a1 = float(a1_str) if a1_str else 0.0
                except ValueError:
                    a1 = 0.0
                    
                try:
                    ref_time_str = line[43:51].strip()
                    ref_time = int(ref_time_str) if ref_time_str else 0
                except ValueError:
                    ref_time = 0
                    
                try:
                    ref_week_str = line[51:60].strip()
                    ref_week = int(ref_week_str) if ref_week_str else 0
                except ValueError:
                    ref_week = 0
                    
                self.header['time_system_corr'][corr_type] = {
                    'a0': a0, 'a1': a1, 'ref_time': ref_time, 'ref_week': ref_week
                }
            elif "LEAP SECONDS" in label:
                self.header['leap_seconds'] = int(line[:6].strip())
            # Add other header items as needed
    
    def _parse_data(self, data_content: str) -> None:
        """
        Parse the data section of a RINEX 3 Navigation file.
        
        Parameters
        ----------
        data_content : str
            String containing the data section of the RINEX file.
        """
        lines = data_content.strip().split('\n')
        
        # Dictionary to store records by satellite system
        records_by_system = {}
        
        i = 0
        while i < len(lines):
            if not lines[i].strip():
                i += 1
                continue
                
            # First line contains epoch and satellite info
            # Format: [SatSystem][PRN] YYYY MM DD HH MM SS.SSSSSSS
            sat_id = lines[i][:3].strip()
            sat_system = sat_id[0]  # First character is the satellite system
            prn = int(sat_id[1:3])
            
            year = int(lines[i][4:8].strip())
            month = int(lines[i][9:11].strip())
            day = int(lines[i][12:14].strip())
            hour = int(lines[i][15:17].strip())
            minute = int(lines[i][18:20].strip())
            second = float(lines[i][21:23].strip())
            
            # Parse SV clock terms with more robust error handling
            def parse_sci_notation(value_str):
                # Handle malformed scientific notation
                value_str = value_str.replace('D', 'E')
                if value_str.endswith('-') and 'E-' in value_str:
                    value_str = value_str[:-1]  # Remove trailing '-'
                elif value_str.endswith('+') and 'E+' in value_str:
                    value_str = value_str[:-1]  # Remove trailing '+'
                return float(value_str)
            
            try:
                sv_clock_bias = parse_sci_notation(lines[i][23:42].strip())
                sv_clock_drift = parse_sci_notation(lines[i][42:61].strip())
                sv_clock_drift_rate = parse_sci_notation(lines[i][61:80].strip())
            except ValueError as e:
                print(f"Warning: Error parsing SV clock parameters: {e}. Using defaults.")
                sv_clock_bias = 0.0
                sv_clock_drift = 0.0
                sv_clock_drift_rate = 0.0
            
            # Process additional lines for orbital parameters
            num_lines = 8  # Default for GPS, QZSS, may vary for other systems
            if sat_system in ['R', 'S']:  # GLONASS, SBAS have 4 lines
                num_lines = 4
            elif sat_system in ['C', 'E', 'I']:  # BeiDou, Galileo, IRNSS have 8 lines
                num_lines = 8
            elif sat_system == 'J':  # QZSS has 8 lines
                num_lines = 8
                
            orbital_params = []
            for j in range(1, num_lines):
                if i + j < len(lines):
                    line = lines[i + j]
                    if not line.strip():
                        continue
                    # Each line has 4 fields
                    for k in range(0, 4):
                        start_idx = k * 19 + 4  # Skip the first 4 characters
                        if start_idx < len(line):
                            end_idx = start_idx + 19
                            if end_idx <= len(line):
                                param_str = line[start_idx:end_idx].strip()
                                if param_str:
                                    try:
                                        param = parse_sci_notation(param_str)
                                    except ValueError:
                                        param = np.nan
                                else:
                                    param = np.nan
                                orbital_params.append(param)
            
            # Create record
            epoch = datetime(year, month, day, hour, minute, int(second),
                           int((second - int(second)) * 1e6))
            
            # Basic record structure (common for all satellite systems)
            record = {
                'PRN': prn,
                'Epoch': epoch,
                'Toc': epoch,
                'SV_clock_bias': sv_clock_bias,
                'SV_clock_drift': sv_clock_drift,
                'SV_clock_drift_rate': sv_clock_drift_rate,
            }
            
            # Add orbital parameters based on satellite system
            if sat_system == 'G' or sat_system == 'J':  # GPS or QZSS
                record.update({
                    'IODE': orbital_params[0] if len(orbital_params) > 0 else np.nan,
                    'Crs': orbital_params[1] if len(orbital_params) > 1 else np.nan,
                    'Delta_n': orbital_params[2] if len(orbital_params) > 2 else np.nan,
                    'M0': orbital_params[3] if len(orbital_params) > 3 else np.nan,
                    'Cuc': orbital_params[4] if len(orbital_params) > 4 else np.nan,
                    'e': orbital_params[5] if len(orbital_params) > 5 else np.nan,
                    'Cus': orbital_params[6] if len(orbital_params) > 6 else np.nan,
                    'sqrt_A': orbital_params[7] if len(orbital_params) > 7 else np.nan,
                    'Toe': orbital_params[8] if len(orbital_params) > 8 else np.nan,
                    'Cic': orbital_params[9] if len(orbital_params) > 9 else np.nan,
                    'OMEGA': orbital_params[10] if len(orbital_params) > 10 else np.nan,
                    'Cis': orbital_params[11] if len(orbital_params) > 11 else np.nan,
                    'i0': orbital_params[12] if len(orbital_params) > 12 else np.nan,
                    'Crc': orbital_params[13] if len(orbital_params) > 13 else np.nan,
                    'omega': orbital_params[14] if len(orbital_params) > 14 else np.nan,
                    'OMEGA_DOT': orbital_params[15] if len(orbital_params) > 15 else np.nan,
                    'IDOT': orbital_params[16] if len(orbital_params) > 16 else np.nan,
                    'L2_codes': orbital_params[17] if len(orbital_params) > 17 else np.nan,
                    'GPS_week': orbital_params[18] if len(orbital_params) > 18 else np.nan,
                    'L2_P_flag': orbital_params[19] if len(orbital_params) > 19 else np.nan,
                    'SV_accuracy': orbital_params[20] if len(orbital_params) > 20 else np.nan,
                    'SV_health': orbital_params[21] if len(orbital_params) > 21 else np.nan,
                    'TGD': orbital_params[22] if len(orbital_params) > 22 else np.nan,
                    'IODC': orbital_params[23] if len(orbital_params) > 23 else np.nan,
                    'Transmission_time': orbital_params[24] if len(orbital_params) > 24 else np.nan,
                    'Fit_interval': orbital_params[25] if len(orbital_params) > 25 else np.nan
                })
            elif sat_system == 'R':  # GLONASS
                record.update({
                    'Tau': orbital_params[0] if len(orbital_params) > 0 else np.nan,
                    'Gamma': orbital_params[1] if len(orbital_params) > 1 else np.nan,
                    'tb': orbital_params[2] if len(orbital_params) > 2 else np.nan,
                    'X': orbital_params[3] if len(orbital_params) > 3 else np.nan,
                    'X_velocity': orbital_params[4] if len(orbital_params) > 4 else np.nan,
                    'X_acceleration': orbital_params[5] if len(orbital_params) > 5 else np.nan,
                    'health': orbital_params[6] if len(orbital_params) > 6 else np.nan,
                    'Y': orbital_params[7] if len(orbital_params) > 7 else np.nan,
                    'Y_velocity': orbital_params[8] if len(orbital_params) > 8 else np.nan,
                    'Y_acceleration': orbital_params[9] if len(orbital_params) > 9 else np.nan,
                    'frequency_number': orbital_params[10] if len(orbital_params) > 10 else np.nan,
                    'Z': orbital_params[11] if len(orbital_params) > 11 else np.nan,
                    'Z_velocity': orbital_params[12] if len(orbital_params) > 12 else np.nan,
                    'Z_acceleration': orbital_params[13] if len(orbital_params) > 13 else np.nan,
                    'Age': orbital_params[14] if len(orbital_params) > 14 else np.nan
                })
            elif sat_system == 'C':  # BeiDou
                record.update({
                    'AODE': orbital_params[0] if len(orbital_params) > 0 else np.nan,
                    'Crs': orbital_params[1] if len(orbital_params) > 1 else np.nan,
                    'Delta_n': orbital_params[2] if len(orbital_params) > 2 else np.nan,
                    'M0': orbital_params[3] if len(orbital_params) > 3 else np.nan,
                    'Cuc': orbital_params[4] if len(orbital_params) > 4 else np.nan,
                    'e': orbital_params[5] if len(orbital_params) > 5 else np.nan,
                    'Cus': orbital_params[6] if len(orbital_params) > 6 else np.nan,
                    'sqrt_A': orbital_params[7] if len(orbital_params) > 7 else np.nan,
                    'Toe': orbital_params[8] if len(orbital_params) > 8 else np.nan,
                    'Cic': orbital_params[9] if len(orbital_params) > 9 else np.nan,
                    'OMEGA': orbital_params[10] if len(orbital_params) > 10 else np.nan,
                    'Cis': orbital_params[11] if len(orbital_params) > 11 else np.nan,
                    'i0': orbital_params[12] if len(orbital_params) > 12 else np.nan,
                    'Crc': orbital_params[13] if len(orbital_params) > 13 else np.nan,
                    'omega': orbital_params[14] if len(orbital_params) > 14 else np.nan,
                    'OMEGA_DOT': orbital_params[15] if len(orbital_params) > 15 else np.nan,
                    'IDOT': orbital_params[16] if len(orbital_params) > 16 else np.nan,
                    'BDT_week': orbital_params[18] if len(orbital_params) > 18 else np.nan,
                    'SV_accuracy': orbital_params[20] if len(orbital_params) > 20 else np.nan,
                    'SatH1': orbital_params[21] if len(orbital_params) > 21 else np.nan,
                    'TGD1': orbital_params[22] if len(orbital_params) > 22 else np.nan,
                    'TGD2': orbital_params[23] if len(orbital_params) > 23 else np.nan,
                    'Transmission_time': orbital_params[24] if len(orbital_params) > 24 else np.nan
                })
            elif sat_system == 'E':  # Galileo
                record.update({
                    'IODnav': orbital_params[0] if len(orbital_params) > 0 else np.nan,
                    'Crs': orbital_params[1] if len(orbital_params) > 1 else np.nan,
                    'Delta_n': orbital_params[2] if len(orbital_params) > 2 else np.nan,
                    'M0': orbital_params[3] if len(orbital_params) > 3 else np.nan,
                    'Cuc': orbital_params[4] if len(orbital_params) > 4 else np.nan,
                    'e': orbital_params[5] if len(orbital_params) > 5 else np.nan,
                    'Cus': orbital_params[6] if len(orbital_params) > 6 else np.nan,
                    'sqrt_A': orbital_params[7] if len(orbital_params) > 7 else np.nan,
                    'Toe': orbital_params[8] if len(orbital_params) > 8 else np.nan,
                    'Cic': orbital_params[9] if len(orbital_params) > 9 else np.nan,
                    'OMEGA': orbital_params[10] if len(orbital_params) > 10 else np.nan,
                    'Cis': orbital_params[11] if len(orbital_params) > 11 else np.nan,
                    'i0': orbital_params[12] if len(orbital_params) > 12 else np.nan,
                    'Crc': orbital_params[13] if len(orbital_params) > 13 else np.nan,
                    'omega': orbital_params[14] if len(orbital_params) > 14 else np.nan,
                    'OMEGA_DOT': orbital_params[15] if len(orbital_params) > 15 else np.nan,
                    'IDOT': orbital_params[16] if len(orbital_params) > 16 else np.nan,
                    'Data_sources': orbital_params[17] if len(orbital_params) > 17 else np.nan,
                    'GAL_week': orbital_params[18] if len(orbital_params) > 18 else np.nan,
                    'SISA': orbital_params[20] if len(orbital_params) > 20 else np.nan,
                    'SV_health': orbital_params[21] if len(orbital_params) > 21 else np.nan,
                    'BGD_E5a_E1': orbital_params[22] if len(orbital_params) > 22 else np.nan,
                    'BGD_E5b_E1': orbital_params[23] if len(orbital_params) > 23 else np.nan,
                    'Transmission_time': orbital_params[24] if len(orbital_params) > 24 else np.nan
                })
            # Add more satellite system mappings as needed (SBAS, IRNSS, etc.)
            
            # Add record to the appropriate satellite system
            if sat_system not in records_by_system:
                records_by_system[sat_system] = []
            
            records_by_system[sat_system].append(record)
            i += num_lines  # Move to the next record
        
        # Convert to DataFrames
        for sys, records in records_by_system.items():
            if records:
                self.data[sys] = pd.DataFrame(records)
            else:
                self.data[sys] = pd.DataFrame()


def read_rinex_nav(filename: str) -> Union[Rinex2NavReader, Rinex3NavReader]:
    """
    Factory function to read a RINEX navigation file and return the appropriate reader instance.
    
    Parameters
    ----------
    filename : str
        Path to the RINEX navigation file.
        
    Returns
    -------
    Union[Rinex2NavReader, Rinex3NavReader]
        Reader instance for the RINEX navigation file.
    
    Raises
    ------
    ValueError
        If the RINEX version is not supported or cannot be determined.
    """
    # Read the first line of the file to determine the RINEX version
    with open(filename, 'r') as f:
        first_line = f.readline()
    
    # Extract version number
    try:
        version = float(first_line[:9].strip())
    except ValueError:
        raise ValueError(f"Cannot determine RINEX version from file: {filename}")
    
    # Select the appropriate reader based on version
    if 2.0 <= version < 3.0:
        return Rinex2NavReader(filename)
    elif version >= 3.0:
        return Rinex3NavReader(filename)
    else:
        raise ValueError(f"Unsupported RINEX version: {version}")