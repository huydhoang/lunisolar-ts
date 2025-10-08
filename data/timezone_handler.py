#!/usr/bin/env python3
"""
Timezone Handler Module
======================

This module provides timezone conversion utilities for the lunisolar calendar system.
It ensures all astronomical calculations are performed in the correct timezone context,
particularly China Standard Time (CST, UTC+8) which is required for traditional
Chinese calendar calculations.

Usage:
    from timezone_handler import TimezoneHandler
    
    # Create handler for CST (UTC+8)
    tz_handler = TimezoneHandler(utc_offset=8)
    
    # Convert local time to UTC for calculations
    utc_time = tz_handler.local_to_utc(local_datetime)
    
    # Convert UTC results back to local time
    local_time = tz_handler.utc_to_local(utc_datetime)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from skyfield.api import utc

from utils import setup_logging


class TimezoneHandler:
    """
    Handles timezone conversions for lunisolar calendar calculations.
    
    The Chinese lunisolar calendar traditionally uses China Standard Time (CST, UTC+8)
    for all astronomical calculations. This class provides utilities to convert between
    local time zones and UTC, ensuring consistent calculation results.
    """
    
    def __init__(self, utc_offset: float = 8.0):
        """
        Initialize the timezone handler.
        
        Args:
            utc_offset: UTC offset in hours (default: 8.0 for CST)
                       Positive values are east of UTC, negative are west.
        """
        self.logger = setup_logging()
        self.utc_offset = utc_offset
        self.timezone = timezone(timedelta(hours=utc_offset))
        
        # Log the timezone being used
        if utc_offset == 8.0:
            self.logger.info("Using China Standard Time (CST, UTC+8) for calculations")
        elif utc_offset == 0.0:
            self.logger.info("Using UTC for calculations")
        else:
            self.logger.info(f"Using UTC{utc_offset:+.1f} for calculations")
    
    def local_to_utc(self, local_datetime: datetime) -> datetime:
        """
        Convert local datetime to UTC.
        
        Args:
            local_datetime: Datetime in the local timezone (naive or timezone-aware)
            
        Returns:
            Datetime in UTC timezone
        """
        try:
            # If datetime is naive, assume it's in the local timezone
            if local_datetime.tzinfo is None:
                local_datetime = local_datetime.replace(tzinfo=self.timezone)
            
            # Convert to UTC
            utc_datetime = local_datetime.astimezone(utc)
            
            self.logger.debug(f"Converted {local_datetime} to UTC: {utc_datetime}")
            return utc_datetime
            
        except Exception as e:
            self.logger.error(f"Error converting local time to UTC: {e}")
            # Fallback: assume input is already UTC
            return local_datetime.replace(tzinfo=utc)
    
    def utc_to_local(self, utc_datetime: datetime) -> datetime:
        """
        Convert UTC datetime to local timezone.
        
        Args:
            utc_datetime: Datetime in UTC timezone
            
        Returns:
            Datetime in the local timezone
        """
        try:
            # Ensure the datetime is timezone-aware and in UTC
            if utc_datetime.tzinfo is None:
                utc_datetime = utc_datetime.replace(tzinfo=utc)
            elif utc_datetime.tzinfo != utc:
                utc_datetime = utc_datetime.astimezone(utc)
            
            # Convert to local timezone
            local_datetime = utc_datetime.astimezone(self.timezone)
            
            self.logger.debug(f"Converted UTC {utc_datetime} to local: {local_datetime}")
            return local_datetime
            
        except Exception as e:
            self.logger.error(f"Error converting UTC to local time: {e}")
            # Fallback: return as-is
            return utc_datetime
    
    def parse_local_datetime(self, date_str: str, time_str: str = "12:00") -> datetime:
        """
        Parse date and time strings as local datetime.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            time_str: Time string in HH:MM format (default: "12:00")
            
        Returns:
            Datetime object in the local timezone
        """
        try:
            # Parse the date and time
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            # Combine and set timezone
            local_datetime = datetime.combine(date_obj, time_obj)
            local_datetime = local_datetime.replace(tzinfo=self.timezone)
            
            self.logger.debug(f"Parsed local datetime: {local_datetime}")
            return local_datetime
            
        except Exception as e:
            self.logger.error(f"Error parsing datetime '{date_str} {time_str}': {e}")
            raise ValueError(f"Invalid date/time format: {date_str} {time_str}")
    
    def get_timezone_info(self) -> dict:
        """
        Get information about the current timezone configuration.
        
        Returns:
            Dictionary with timezone information
        """
        return {
            'utc_offset': self.utc_offset,
            'timezone_name': self._get_timezone_name(),
            'is_cst': self.utc_offset == 8.0,
            'offset_string': f"UTC{self.utc_offset:+.1f}"
        }
    
    def _get_timezone_name(self) -> str:
        """
        Get a human-readable timezone name.
        
        Returns:
            Timezone name string
        """
        if self.utc_offset == 8.0:
            return "China Standard Time (CST)"
        elif self.utc_offset == 0.0:
            return "Coordinated Universal Time (UTC)"
        elif self.utc_offset == -5.0:
            return "Eastern Standard Time (EST)"
        elif self.utc_offset == -8.0:
            return "Pacific Standard Time (PST)"
        else:
            return f"UTC{self.utc_offset:+.1f}"
    
    @staticmethod
    def create_cst_handler() -> 'TimezoneHandler':
        """
        Create a timezone handler configured for China Standard Time.
        
        Returns:
            TimezoneHandler instance for CST (UTC+8)
        """
        return TimezoneHandler(utc_offset=8.0)
    
    @staticmethod
    def create_utc_handler() -> 'TimezoneHandler':
        """
        Create a timezone handler configured for UTC.
        
        Returns:
            TimezoneHandler instance for UTC
        """
        return TimezoneHandler(utc_offset=0.0)
    
    @staticmethod
    def create_from_utc_offset(utc_offset: float) -> 'TimezoneHandler':
        """
        Create a timezone handler from a UTC offset.
        
        Args:
            utc_offset: UTC offset in hours (e.g., 8.0 for UTC+8)
            
        Returns:
            TimezoneHandler instance for the specified offset
        """
        return TimezoneHandler(utc_offset=utc_offset)
    
    def validate_timezone_sensitivity(self, test_datetime: datetime) -> dict:
        """
        Test timezone sensitivity for a given datetime.
        
        This method helps identify cases where timezone differences might affect
        calendar calculations, particularly around new moon and solar term boundaries.
        
        Args:
            test_datetime: Datetime to test
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        results = {
            'input_datetime': test_datetime,
            'local_timezone': self._get_timezone_name(),
            'utc_equivalent': self.local_to_utc(test_datetime),
            'timezone_sensitive': False,
            'notes': []
        }
        
        # Check if we're near midnight (when date changes)
        local_hour = test_datetime.hour
        if local_hour <= 2 or local_hour >= 22:
            results['timezone_sensitive'] = True
            results['notes'].append("Near midnight - timezone may affect date calculation")
        
        # Check UTC offset impact
        utc_equiv = self.local_to_utc(test_datetime)
        if utc_equiv.date() != test_datetime.date():
            results['timezone_sensitive'] = True
            results['notes'].append(f"Date changes from {test_datetime.date()} to {utc_equiv.date()} in UTC")
        
        return results


def get_default_timezone_handler() -> TimezoneHandler:
    """
    Get the default timezone handler for Chinese calendar calculations.
    
    Returns:
        TimezoneHandler configured for China Standard Time (CST, UTC+8)
    """
    return TimezoneHandler.create_cst_handler()


def parse_utc_offset_argument(utc_arg: Union[str, int, float]) -> float:
    """
    Parse UTC offset argument from command line.
    
    Supports formats:
    - Numeric: 8, -5, 8.5
    - String with sign: '+08:00', '-05:00', '+8', '-5'
    
    Args:
        utc_arg: UTC offset as string, int, or float
        
    Returns:
        UTC offset as float
        
    Raises:
        ValueError: If the argument cannot be parsed as a valid UTC offset
    """
    try:
        # Handle string formats like '+08:00', '-05:00'
        if isinstance(utc_arg, str):
            utc_str = utc_arg.strip()
            
            # Handle HH:MM format
            if ':' in utc_str:
                # Parse '+08:00' or '-05:00' format
                if utc_str.startswith(('+', '-')):
                    sign = 1 if utc_str[0] == '+' else -1
                    time_part = utc_str[1:]
                else:
                    sign = 1
                    time_part = utc_str
                
                # Split hours and minutes
                if ':' in time_part:
                    hours_str, minutes_str = time_part.split(':', 1)
                    hours = int(hours_str)
                    minutes = int(minutes_str)
                    offset = sign * (hours + minutes / 60.0)
                else:
                    raise ValueError("Invalid time format")
            else:
                # Handle simple numeric string like '+8', '-5'
                offset = float(utc_str)
        else:
            # Handle numeric types
            offset = float(utc_arg)
        
        # Validate reasonable range (-12 to +14 hours)
        if not -12.0 <= offset <= 14.0:
            raise ValueError(f"UTC offset {offset} is outside valid range (-12 to +14)")
        
        return offset
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid UTC offset '{utc_arg}': expected format like '+08:00', '-05:00', or numeric value between -12 and +14")


if __name__ == "__main__":
    # Example usage and testing
    import sys
    
    # Test with different timezones
    timezones_to_test = [0.0, 8.0, -5.0, -8.0]
    test_datetime = datetime(2025, 7, 25, 12, 0)
    
    print("Timezone Handler Testing")
    print("=" * 40)
    
    for tz_offset in timezones_to_test:
        handler = TimezoneHandler(tz_offset)
        info = handler.get_timezone_info()
        
        print(f"\nTimezone: {info['timezone_name']}")
        print(f"UTC Offset: {info['offset_string']}")
        
        local_dt = test_datetime.replace(tzinfo=handler.timezone)
        utc_dt = handler.local_to_utc(local_dt)
        back_to_local = handler.utc_to_local(utc_dt)
        
        print(f"Local time: {local_dt}")
        print(f"UTC time: {utc_dt}")
        print(f"Back to local: {back_to_local}")
        
        # Test sensitivity
        sensitivity = handler.validate_timezone_sensitivity(local_dt)
        if sensitivity['timezone_sensitive']:
            print(f"⚠️  Timezone sensitive: {', '.join(sensitivity['notes'])}")
        else:
            print("✅ Not timezone sensitive")