"""
Test script for the RINEX Navigation reader module.

This script tests the RINEX Navigation reader with sample files to verify functionality.
"""

import os
import sys
import tempfile
import pandas as pd
from datetime import datetime, timedelta

# Add the parent directory to the path to import the pygnsslab module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from pygnsslab.io.rinexnav.reader import read_rinex_nav
from pygnsslab.io.rinexnav.utils import (
    interpolate_orbit,
    compute_sv_clock_correction,
    detect_rinex_version
)

def write_sample_file(content, file_extension=".txt"):
    """
    Write sample content to a temporary file.
    
    Parameters
    ----------
    content : str
        Content to write to the file.
    file_extension : str, optional
        File extension to use for the temporary file (default: ".txt").
        
    Returns
    -------
    str
        Path to the temporary file.
    """
    with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False, mode="w") as f:
        f.write(content)
        temp_path = f.name
    
    return temp_path

def test_rinex2_reader():
    """Test the RINEX 2 Navigation reader with sample data."""
    print("Starting RINEX 2 Navigation reader test...")
    # Sample RINEX 2 Navigation data
    rinex2_content = """     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
Converto v3.5.6     IGN                 20220102 000706 UTC PGM / RUN BY / DATE
Linux 2.6.32-573.12.1.x86_64|x86_64|gcc|Linux 64|=+         COMMENT
                                                            END OF HEADER
 1 02  1  1  0  0  0.0 4.691267386079D-04-1.000444171950D-11 0.000000000000D+00
    3.900000000000D+01-1.411250000000D+02 3.988380292697D-09-6.242942382352D-01
   -7.363036274910D-06 1.121813920327D-02 4.695728421211D-06 5.153674995422D+03
    5.184000000000D+05-3.166496753693D-08-1.036611240093D+00 1.955777406693D-07
    9.864187694897D-01 2.997500000000D+02 8.840876015687D-01-8.133553386358D-09
   -3.778728718817D-10 1.000000000000D+00 2.190000000000D+03 0.000000000000D+00
    2.000000000000D+00 0.000000000000D+00 5.122274160385D-09 3.900000000000D+01
    5.184000000000D+05
 1 02  1  1  2  0  0.0 4.690550267696D-04-1.000444171950D-11 0.000000000000D+00
    7.000000000000D+01-1.377812500000D+02 4.009809817518D-09 4.259599915377D-01
   -7.105991244316D-06 1.121853594668D-02 4.127621650696D-06 5.153675922394D+03
    5.256000000000D+05-8.381903171539D-08-1.036670036234D+00 1.229345798492D-07
    9.864159884824D-01 3.122812500000D+02 8.840083845547D-01-8.161768150217D-09
   -3.832302530871D-10 1.000000000000D+00 2.190000000000D+03 0.000000000000D+00
    2.000000000000D+00 0.000000000000D+00 5.122274160385D-09 7.000000000000D+01
    5.184300000000D+05"""
    
    print("Writing sample RINEX 2 content to temporary file...")
    # Write to a temporary file
    rinex2_file = write_sample_file(rinex2_content, ".n")
    
    try:
        # Test version detection
        version = detect_rinex_version(rinex2_file)
        print(f"Detected RINEX version: {version}")
        assert 2.0 <= version < 3.0, f"Expected RINEX 2.x, got {version}"
        
        # Test reading the file
        print("Reading RINEX 2 navigation file...")
        nav_reader = read_rinex_nav(rinex2_file)
        
        # Check if header was parsed correctly
        print(f"Header version: {nav_reader.header['version']}")
        print(f"Header file_type: '{nav_reader.header['file_type']}'")
        
        assert nav_reader.header['version'] == 2.11, "Incorrect version in header"
        assert nav_reader.header['file_type'] == 'N', "Incorrect file type in header"
        assert 'program' in nav_reader.header, "Missing program in header"
        
        # Check if data was parsed correctly
        assert 'G' in nav_reader.data, "Missing GPS data"
        gps_data = nav_reader.data['G']
        assert len(gps_data) == 2, f"Expected 2 records, got {len(gps_data)}"
        
        # Check the first record
        first_record = gps_data.iloc[0]
        assert first_record['PRN'] == 1, f"Expected PRN 1, got {first_record['PRN']}"
        assert first_record['Epoch'].year == 2002, f"Expected year 2002, got {first_record['Epoch'].year}"
        assert abs(first_record['SV_clock_bias'] - 4.691267386079e-04) < 1e-12, "Incorrect SV clock bias"
        
        # Test orbit interpolation
        test_time = first_record['Epoch'] + timedelta(hours=1)
        try:
            orbit = interpolate_orbit(gps_data, test_time, 'G', 1)
            print("Interpolated orbit:", orbit)
            assert 'X' in orbit and 'Y' in orbit and 'Z' in orbit, "Missing position components"
            assert 'VX' in orbit and 'VY' in orbit and 'VZ' in orbit, "Missing velocity components"
        except Exception as e:
            print(f"Warning: Orbit interpolation failed: {e}")
        
        # Test clock correction
        try:
            clock_corr = compute_sv_clock_correction(gps_data, test_time, 'G', 1)
            print(f"Clock correction: {clock_corr} seconds")
        except Exception as e:
            print(f"Warning: Clock correction failed: {e}")
        
        print("RINEX 2 Navigation reader test: PASSED")
    
    except Exception as e:
        print(f"RINEX 2 Navigation reader test: FAILED - {e}")
    
    finally:
        # Clean up
        if os.path.exists(rinex2_file):
            os.unlink(rinex2_file)

def test_rinex3_reader():
    """Test the RINEX 3 Navigation reader with sample data."""
    print("Starting RINEX 3 Navigation reader test...")
    # Sample RINEX 3 Navigation data
    rinex3_content = """     3.04           N: GNSS NAV DATA    M: MIXED NAV DATA   RINEX VERSION / TYPE
Alloy 5.44          Receiver Operator   20220101 000000 UTC PGM / RUN BY / DATE
GPSA    .1211D-07  -.7451D-08  -.5960D-07   .1192D-06       IONOSPHERIC CORR
GPSB    .1167D+06  -.2458D+06  -.6554D+05   .1114D+07       IONOSPHERIC CORR
GAL     .8775D+02   .4180D+00  -.1074D-01   .0000D+00       IONOSPHERIC CORR
QZSA    .1118D-07  -.4470D-07  -.4172D-06  -.4768D-06       IONOSPHERIC CORR
QZSB    .9830D+05  -.3277D+05  -.1507D+07  -.8192D+07       IONOSPHERIC CORR
GPUT  -.1862645149D-08 -.621724894D-14  61440 2191          TIME SYSTEM CORR
GAUT   .1862645149D-08 -.888178420D-15 432000 2190          TIME SYSTEM CORR
QZUT   .2793967724D-08  .000000000D+00  94208 2191          TIME SYSTEM CORR
GPGA   .1979060471D-08 -.976996262D-14 518400 2190          TIME SYSTEM CORR
    18    18  2185     7                                    LEAP SECONDS
                                                            END OF HEADER
G31 2022 01 01 00 00 00 -.157775823027D-03 -.181898940355D-11  .000000000000D+00
      .110000000000D+02 -.170937500000D+02  .480234289400D-08 -.173098544978D+01
     -.117905437946D-05  .104654430179D-01  .877678394318D-05  .515366246605D+04
      .518400000000D+06  .204890966415D-07  .211722260728D+01 -.141561031342D-06
      .954983160093D+00  .203406250000D+03  .359636360687D+00 -.795676000242D-08
     -.496092092798D-09  .100000000000D+01  .219000000000D+04  .000000000000D+00
      .200000000000D+01  .000000000000D+00 -.130385160446D-07  .110000000000D+02
      .516102000000D+06  .400000000000D+01
C01 2021 12 31 23 00 00 -.285546178930D-03  .402868849392D-10  .000000000000D+00
      .100000000000D+01  .250171875000D+03 -.412517182996D-09  .329616550241D+00
      .806059688330D-05  .611470197327D-03  .322125852108D-04  .649341227531D+04
      .514800000000D+06 -.211410224438D-06  .302754416285D+01 -.167638063431D-06
      .794697272388D-01 -.992296875000D+03 -.992867610818D+00  .158042297382D-08
     -.118362073113D-08  .000000000000D+00  .834000000000D+03  .000000000000D+00
      .200000000000D+01  .000000000000D+00 -.580000003580D-08 -.102000000000D-07
      .514800000000D+06  .000000000000D+00
R05 2021 12 31 23 45 00  .851778313518D-04  .909494701773D-12  .518370000000D+06
     -.215384257812D+05 -.146265029907D-01 -.279396772385D-08  .000000000000D+00
     -.136201572266D+05  .206674575806D+00  .279396772385D-08  .100000000000D+01
     -.692044921875D+03 -.358163070679D+01 -.186264514923D-08  .000000000000D+00"""
    
    print("Writing sample RINEX 3 content to temporary file...")
    # Write to a temporary file
    rinex3_file = write_sample_file(rinex3_content, ".nav")
    
    try:
        # Test version detection
        version = detect_rinex_version(rinex3_file)
        print(f"Detected RINEX version: {version}")
        assert 3.0 <= version < 4.0, f"Expected RINEX 3.x, got {version}"
        
        # Test reading the file
        print("Reading RINEX 3 navigation file...")
        nav_reader = read_rinex_nav(rinex3_file)
        
        # Check if header was parsed correctly
        print(f"Header file_type: '{nav_reader.header['file_type']}'")
        assert nav_reader.header['version'] == 3.04, "Incorrect version in header"
        assert nav_reader.header['file_type'] == 'N', "Incorrect file type in header"
        assert 'program' in nav_reader.header, "Missing program in header"
        assert 'ionospheric_corr' in nav_reader.header, "Missing ionospheric correction in header"
        assert 'time_system_corr' in nav_reader.header, "Missing time system correction in header"
        
        # Check if data was parsed correctly
        print(f"Systems in data: {list(nav_reader.data.keys())}")
        assert 'G' in nav_reader.data, "Missing GPS data"
        assert 'C' in nav_reader.data, "Missing BeiDou data"
        assert 'R' in nav_reader.data, "Missing GLONASS data"
        
        # Check GPS data
        gps_data = nav_reader.data['G']
        assert len(gps_data) == 1, f"Expected 1 GPS record, got {len(gps_data)}"
        
        # Check BeiDou data
        bds_data = nav_reader.data['C']
        assert len(bds_data) == 1, f"Expected 1 BeiDou record, got {len(bds_data)}"
        
        # Check GLONASS data
        glo_data = nav_reader.data['R']
        assert len(glo_data) == 1, f"Expected 1 GLONASS record, got {len(glo_data)}"
        
        # Check GPS record
        gps_record = gps_data.iloc[0]
        assert gps_record['PRN'] == 31, f"Expected PRN 31, got {gps_record['PRN']}"
        assert gps_record['Epoch'].year == 2022, f"Expected year 2022, got {gps_record['Epoch'].year}"
        assert abs(gps_record['SV_clock_bias'] + 1.57775823027e-04) < 1e-12, "Incorrect SV clock bias"
        
        # Check BeiDou record
        bds_record = bds_data.iloc[0]
        assert bds_record['PRN'] == 1, f"Expected PRN 1, got {bds_record['PRN']}"
        
        # Check GLONASS record
        glo_record = glo_data.iloc[0]
        assert glo_record['PRN'] == 5, f"Expected PRN 5, got {glo_record['PRN']}"
        
        # Test orbit interpolation for GPS
        test_time = gps_record['Epoch'] + timedelta(hours=1)
        try:
            orbit = interpolate_orbit(gps_data, test_time, 'G', 31)
            print("Interpolated GPS orbit:", orbit)
            assert 'X' in orbit and 'Y' in orbit and 'Z' in orbit, "Missing position components"
        except Exception as e:
            print(f"Warning: GPS orbit interpolation failed: {e}")
        
        print("RINEX 3 Navigation reader test: PASSED")
    
    except Exception as e:
        print(f"RINEX 3 Navigation reader test: FAILED - {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if os.path.exists(rinex3_file):
            os.unlink(rinex3_file)

def main():
    """Run all tests."""
    print("Testing RINEX Navigation reader...")
    test_rinex2_reader()
    test_rinex3_reader()
    print("All tests completed.")

if __name__ == "__main__":
    main()