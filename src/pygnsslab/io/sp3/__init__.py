"""
SP3 (Standard Product 3) file I/O module.

This module provides functionality to read and write SP3 format files,
which contain precise GNSS satellite orbit and clock information.

The module supports both SP3-c and SP3-d formats.
"""

from .reader import SP3Reader
from .writer import SP3Writer, write_sp3_file
from .metadata import SP3Header, SP3Epoch, SP3SatelliteRecord
from .utils import identify_sp3_version

__all__ = [
    'SP3Reader',
    'SP3Writer',
    'write_sp3_file',
    'SP3Header',
    'SP3Epoch',
    'SP3SatelliteRecord',
    'identify_sp3_version'
]