#!/usr/bin/env python3
"""
Lunisolar Calendar Engine v2
============================

A clean, modular implementation of the lunisolar calendar conversion system
following the blueprint architecture and adhering to traditional Chinese
calendar rules.

This module implements:
- Strict CST date-only comparisons for month boundaries
- No-zhongqi rule for leap month determination
- Local solar time for hour calculations
- Sexagenary cycle calculations with proper anchors
- Modular architecture with clear separation of concerns

Usage:
    from lunisolar_v2 import solar_to_lunisolar
    result = solar_to_lunisolar("2025-01-15", "14:30")
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging
from skyfield.api import utc, load
from skyfield import almanac

from config import EPHEMERIS_FILE
from utils import setup_logging
from solar_terms import calculate_solar_terms
from moon_phases import calculate_moon_phases
from timezone_handler import TimezoneHandler


# Constants from traditional Chinese calendar
HEAVENLY_STEMS = [
    ('甲', 'jiǎ', 'Wood Yang', 1),
    ('乙', 'yǐ', 'Wood Yin', 2),
    ('丙', 'bǐng', 'Fire Yang', 3),
    ('丁', 'dīng', 'Fire Yin', 4),
    ('戊', 'wù', 'Earth Yang', 5),
    ('己', 'jǐ', 'Earth Yin', 6),
    ('庚', 'gēng', 'Metal Yang', 7),
    ('辛', 'xīn', 'Metal Yin', 8),
    ('壬', 'rén', 'Water Yang', 9),
    ('癸', 'guǐ', 'Water Yin', 10)
]

EARTHLY_BRANCHES = [
    ('子', 'zǐ', 'Rat', 1, 23, 1),      # 23:00-01:00
    ('丑', 'chǒu', 'Ox', 2, 1, 3),      # 01:00-03:00
    ('寅', 'yín', 'Tiger', 3, 3, 5),    # 03:00-05:00
    ('卯', 'mǎo', 'Rabbit', 4, 5, 7),   # 05:00-07:00
    ('辰', 'chén', 'Dragon', 5, 7, 9),  # 07:00-09:00
    ('巳', 'sì', 'Snake', 6, 9, 11),    # 09:00-11:00
    ('午', 'wǔ', 'Horse', 7, 11, 13),   # 11:00-13:00
    ('未', 'wèi', 'Goat', 8, 13, 15),   # 13:00-15:00
    ('申', 'shēn', 'Monkey', 9, 15, 17), # 15:00-17:00
    ('酉', 'yǒu', 'Rooster', 10, 17, 19), # 17:00-19:00
    ('戌', 'xū', 'Dog', 11, 19, 21),    # 19:00-21:00
    ('亥', 'hài', 'Pig', 12, 21, 23)    # 21:00-23:00
]

# Principal Solar Terms (Z1-Z12) for leap month determination
PRINCIPAL_TERMS = {
    1: 330,   # Z1 雨水 Rain Water
    2: 0,     # Z2 春分 Spring Equinox
    3: 30,    # Z3 穀雨 Grain Rain
    4: 60,    # Z4 小滿 Grain Full
    5: 90,    # Z5 夏至 Summer Solstice
    6: 120,   # Z6 大暑 Great Heat
    7: 150,   # Z7 處暑 Limit of Heat
    8: 180,   # Z8 秋分 Autumnal Equinox
    9: 210,   # Z9 霜降 Descent of Frost
    10: 240,  # Z10 小雪 Slight Snow
    11: 270,  # Z11 冬至 Winter Solstice
    12: 300   # Z12 大寒 Great Cold
}


# Data Models
@dataclass(frozen=True)
class PrincipalTerm:
    """Represents a principal solar term with UTC instant and CST date."""
    instant_utc: datetime
    cst_date: date
    term_index: int  # 1..12 for Z1..Z12


@dataclass
class MonthPeriod:
    """Represents a lunar month period with boundaries and term mapping."""
    index: int
    start_utc: datetime
    end_utc: datetime
    start_cst_date: date
    end_cst_date: date
    has_principal_term: bool = False
    is_leap: bool = False
    month_number: int = 0  # 1..12, with Zi month=11


@dataclass(frozen=True)
class LunisolarDateDTO:
    """Complete lunisolar date with stems, branches, and cycles."""
    year: int
    month: int
    day: int
    hour: int
    is_leap_month: bool
    year_stem: str
    year_branch: str
    month_stem: str
    month_branch: str
    day_stem: str
    day_branch: str
    hour_stem: str
    hour_branch: str
    year_cycle: int
    month_cycle: int
    day_cycle: int
    hour_cycle: int


class TimezoneService:
    """Handles timezone conversions and CST date-only comparisons."""
    
    def __init__(self, timezone_handler: Optional[TimezoneHandler] = None):
        self.logger = setup_logging()
        self.tz_handler = timezone_handler or TimezoneHandler.create_cst_handler()
    
    def utc_to_cst_date(self, utc_datetime: datetime) -> date:
        """Convert UTC datetime to CST date for date-only comparisons."""
        cst_datetime = utc_datetime + timedelta(hours=8)
        return cst_datetime.date()
    
    def parse_local_datetime(self, date_str: str, time_str: str = "12:00") -> datetime:
        """Parse local date/time string to datetime object."""
        return self.tz_handler.parse_local_datetime(date_str, time_str)
    
    def local_to_utc(self, local_datetime: datetime) -> datetime:
        """Convert local datetime to UTC for astronomical calculations."""
        return self.tz_handler.local_to_utc(local_datetime)


class WindowPlanner:
    """Plans calculation windows around Winter Solstice anchors."""
    
    def __init__(self):
        self.logger = setup_logging()
    
    def compute_window(self, target_utc: datetime) -> Tuple[datetime, datetime]:
        """Return [start, end] window framing two consecutive Winter Solstices
        surrounding the target date, expanded by ±30 days to catch edge events.
        Uses Skyfield seasons anchor to find Z11 months."""
        # Ensure target is timezone-naive for comparison
        if target_utc.tzinfo is not None:
            target_naive = target_utc.replace(tzinfo=None)
        else:
            target_naive = target_utc
            
        target_year = target_naive.year
        
        # Find Winter Solstices for current and adjacent years
        solstice_current = self._find_winter_solstice(target_year)
        solstice_prev = self._find_winter_solstice(target_year - 1)
        solstice_next = self._find_winter_solstice(target_year + 1)
        
        # Determine which solstice pair to use
        if target_naive >= solstice_current:
            anchor_start = solstice_current
            anchor_end = solstice_next
        else:
            anchor_start = solstice_prev
            anchor_end = solstice_current
        
        # Expand window by 30 days on each side
        window_start = anchor_start - timedelta(days=30)
        window_end = anchor_end + timedelta(days=30)
        
        self.logger.debug(f"Computed window: {window_start} to {window_end}")
        return window_start, window_end
    
    def _find_winter_solstice(self, year: int) -> datetime:
        """Find Winter Solstice for a given year."""
        try:
            ts = load.timescale()
            eph = load(EPHEMERIS_FILE)
            
            t0 = ts.utc(year, 1, 1)
            t1 = ts.utc(year + 1, 1, 1)
            t, y = almanac.find_discrete(t0, t1, almanac.seasons(eph))
            
            for time, season in zip(t, y):
                if season == 3:  # Winter solstice
                    # Use utc_datetime() method to get proper UTC datetime
                    solstice_datetime = time.utc_datetime()
                    return solstice_datetime.replace(tzinfo=None)  # Ensure timezone-naive
            
            raise ValueError(f"Winter solstice not found for year {year}")
        except Exception as e:
            self.logger.error(f"Error finding winter solstice for {year}: {e}")
            raise
        finally:
            if 'eph' in locals():
                del eph


class EphemerisService:
    """Single-pass computation of new moons and principal terms."""
    
    def __init__(self):
        self.logger = setup_logging()
    
    def compute_new_moons(self, start: datetime, end: datetime) -> List[datetime]:
        """Return sorted UTC instants of new moons in [start, end].
        One pass only per window."""
        try:
            # Ensure timezone-aware datetimes for moon_phases calculation
            if start.tzinfo is None:
                start_aware = start.replace(tzinfo=utc)
            else:
                start_aware = start
                
            if end.tzinfo is None:
                end_aware = end.replace(tzinfo=utc)
            else:
                end_aware = end
            
            moon_phases = calculate_moon_phases(start_aware, end_aware)
            new_moons = []
            
            for timestamp, phase_index, phase_name in moon_phases:
                if phase_index == 0:  # New moon
                    # Create timezone-naive UTC datetime
                    new_moon_dt = datetime.fromtimestamp(timestamp, tz=utc).replace(tzinfo=None)
                    new_moons.append(new_moon_dt)
            
            return sorted(new_moons)
        except Exception as e:
            self.logger.error(f"Error computing new moons: {e}")
            return []
    
    def compute_principal_terms(self, start: datetime, end: datetime) -> List[PrincipalTerm]:
        """Return principal terms (Z1..Z12) with UTC instants and CST dates
        precomputed for date-only mapping."""
        try:
            # Ensure timezone-aware datetimes for solar_terms calculation
            if start.tzinfo is None:
                start_aware = start.replace(tzinfo=utc)
            else:
                start_aware = start
                
            if end.tzinfo is None:
                end_aware = end.replace(tzinfo=utc)
            else:
                end_aware = end
            
            solar_terms = calculate_solar_terms(start_aware, end_aware)
            principal_terms = []
            
            for timestamp, idx, zht, zhs, vn in solar_terms:
                # Principal terms are at even indices (0, 2, 4, ..., 22)
                if idx % 2 == 0:
                    # Create timezone-naive UTC datetime
                    term_datetime = datetime.fromtimestamp(timestamp, tz=utc).replace(tzinfo=None)
                    principal_term_number = (idx // 2) + 1
                    if principal_term_number > 12:
                        principal_term_number -= 12
                    
                    # Precompute CST date for date-only comparisons
                    cst_date = (term_datetime + timedelta(hours=8)).date()
                    
                    principal_terms.append(PrincipalTerm(
                        instant_utc=term_datetime,
                        cst_date=cst_date,
                        term_index=principal_term_number
                    ))
            
            return principal_terms
        except Exception as e:
            self.logger.error(f"Error computing principal terms: {e}")
            return []


class MonthBuilder:
    """Builds MonthPeriod objects from new moon sequences."""
    
    def __init__(self, timezone_service: TimezoneService):
        self.logger = setup_logging()
        self.tz_service = timezone_service
    
    def build_month_periods(self, new_moons: List[datetime]) -> List[MonthPeriod]:
        """Build consecutive MonthPeriods from successive new moon instants,
        carrying both UTC and CST date boundaries."""
        periods = []
        
        for i in range(len(new_moons) - 1):
            start_utc = new_moons[i]
            end_utc = new_moons[i + 1]
            
            start_cst_date = self.tz_service.utc_to_cst_date(start_utc)
            end_cst_date = self.tz_service.utc_to_cst_date(end_utc)
            
            period = MonthPeriod(
                index=i,
                start_utc=start_utc,
                end_utc=end_utc,
                start_cst_date=start_cst_date,
                end_cst_date=end_cst_date
            )
            periods.append(period)
        
        self.logger.debug(f"Built {len(periods)} month periods")
        return periods


class TermIndexer:
    """Maps principal terms to lunar months using date-only CST comparisons."""
    
    def __init__(self):
        self.logger = setup_logging()
    
    def tag_principal_terms(self, periods: List[MonthPeriod], terms: List[PrincipalTerm]) -> None:
        """For each term, find the MonthPeriod whose CST startDate <= term.cstDate < endDate.
        If term.cstDate == period.endCstDate, skip (belongs to next month). Set period.hasPrincipalTerm = True."""
        for term in terms:
            for period in periods:
                # Date-only comparison: term belongs to month if it falls within the period
                # but NOT if it falls on the end date (belongs to next month)
                if (period.start_cst_date <= term.cst_date < period.end_cst_date):
                    period.has_principal_term = True
                    self.logger.debug(f"Term Z{term.term_index} mapped to month period {period.index}")
                    break


class LeapMonthAssigner:
    """Assigns month numbers and leap status using no-zhongqi rule."""
    
    def __init__(self):
        self.logger = setup_logging()
    
    def assign_month_numbers(self, periods: List[MonthPeriod], anchor_solstice_utc: datetime) -> None:
        """Locate Zi-month (period containing Winter Solstice) and set number=11.
        Iterate forward:
        - If hasPrincipalTerm: increment sequence (11->12->1->...)
        - Else: mark isLeap=True and assign same number as previous regular month
        Zi-month cannot be leap."""
        
        # Find Zi month (contains Winter Solstice)
        zi_month_index = self._find_zi_month(periods, anchor_solstice_utc)
        if zi_month_index == -1:
            raise ValueError("Could not find Zi month containing Winter Solstice")
        
        # Assign Zi month
        periods[zi_month_index].month_number = 11
        periods[zi_month_index].is_leap = False
        
        # Assign subsequent months
        current_month_number = 11
        for i in range(zi_month_index + 1, len(periods)):
            period = periods[i]
            
            if period.has_principal_term:
                # Regular month - increment number
                current_month_number = (current_month_number % 12) + 1
                period.month_number = current_month_number
                period.is_leap = False
            else:
                # Leap month - takes previous month number
                period.month_number = current_month_number
                period.is_leap = True
        
        # Assign preceding months (if target is before Zi month)
        current_month_number = 11
        for i in range(zi_month_index - 1, -1, -1):
            period = periods[i]
            current_month_number = (current_month_number - 1) if current_month_number > 1 else 12
            
            if period.has_principal_term:
                # Regular month
                period.month_number = current_month_number
                period.is_leap = False
            else:
                # Leap month - takes following month number
                next_month_number = (current_month_number % 12) + 1
                period.month_number = next_month_number
                period.is_leap = True
    
    def _find_zi_month(self, periods: List[MonthPeriod], anchor_solstice_utc: datetime) -> int:
        """Find the month period that contains the Winter Solstice."""
        # Ensure timezone-naive comparison
        if anchor_solstice_utc.tzinfo is not None:
            solstice_naive = anchor_solstice_utc.replace(tzinfo=None)
        else:
            solstice_naive = anchor_solstice_utc
            
        for i, period in enumerate(periods):
            if period.start_utc <= solstice_naive < period.end_utc:
                return i
        return -1


class SexagenaryEngine:
    """Calculates sexagenary cycles for year, month, day, and hour."""
    
    def __init__(self, timezone_service: TimezoneService):
        self.logger = setup_logging()
        self.tz_service = timezone_service
    
    def ganzhi_year(self, lunar_year: int) -> Tuple[str, str, int]:
        """Use 4 AD as authoritative Jiazi anchor; return (stem, branch, cycleIndex 1..60)."""
        year_cycle = (lunar_year - 4) % 60 + 1
        if year_cycle <= 0:
            year_cycle += 60
        
        stem_char, branch_char, _, _ = self._get_stem_branch(year_cycle)
        return stem_char, branch_char, year_cycle
    
    def ganzhi_month(self, lunar_year: int, lunar_month: int) -> Tuple[str, str, int]:
        """Calculate month stem and branch using traditional rules based on year stem."""
        # Get year stem for month stem calculation
        year_stem, _, _ = self.ganzhi_year(lunar_year)
        year_stem_idx = next((i for i, (char, _, _, _) in enumerate(HEAVENLY_STEMS) if char == year_stem), 0) + 1
        
        # Traditional month stem calculation mapping
        mapping_first_month_stem = {
            1: 3, 6: 3,   # 甲/己 -> 丙 (index 3)
            2: 5, 7: 5,   # 乙/庚 -> 戊 (index 5)
            3: 7, 8: 7,   # 丙/辛 -> 庚 (index 7)
            4: 9, 9: 9,   # 丁/壬 -> 壬 (index 9)
            5: 1, 10: 1,  # 戊/癸 -> 甲 (index 1)
        }
        
        first_month_stem_idx = mapping_first_month_stem[year_stem_idx]
        month_stem_idx = ((first_month_stem_idx - 1 + (lunar_month - 1)) % 10) + 1
        
        # Month branch calculation
        month_branch_idx = (lunar_month + 2) % 12
        if month_branch_idx == 0:
            month_branch_idx = 12
        
        # Get stem and branch characters
        month_stem_char = HEAVENLY_STEMS[month_stem_idx - 1][0]
        month_branch_char = EARTHLY_BRANCHES[month_branch_idx - 1][0]
        
        # Calculate month cycle from stem-branch pair
        month_cycle = self._calculate_cycle_from_stem_branch(month_stem_idx, month_branch_idx)
        
        return month_stem_char, month_branch_char, month_cycle
    
    def ganzhi_day(self, target_local: datetime) -> Tuple[str, str, int]:
        """Day cycle using continuous count and documented historical anchors.
        Note: Keep canonical anchor date per rules doc."""
        # Reference: January 31, 4 AD (Jiazi day)
        reference_date = datetime(4, 1, 31)
        
        # Ensure both datetimes are timezone-naive for comparison
        if target_local.tzinfo is not None:
            target_date = target_local.replace(tzinfo=None)
        else:
            target_date = target_local
        
        target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        days_diff = (target_date - reference_date).days
        day_cycle = (days_diff + 1) % 60 + 1
        
        stem_char, branch_char, _, _ = self._get_stem_branch(day_cycle)
        return stem_char, branch_char, day_cycle
    
    def ganzhi_hour(self, target_local_solar_time: datetime, base_day_stem: str) -> Tuple[str, str, int]:
        """Apply Wu Shu Dun; for 23:00–23:59, advance day before computing hour stem/branch.
        Use local solar time per rules."""
        # Ensure timezone-naive datetime for calculations
        if target_local_solar_time.tzinfo is not None:
            local_time = target_local_solar_time.replace(tzinfo=None)
        else:
            local_time = target_local_solar_time
            
        hour = local_time.hour
        minute = local_time.minute
        
        # Get hour branch
        hour_branch_char, hour_branch_name, hour_branch_index = self._get_hour_branch(hour, minute)
        
        # Handle 23:00-23:59 boundary (belongs to next day's Zi hour)
        if hour >= 23:
            # Advance to next day for stem calculation
            next_day = local_time + timedelta(days=1)
            next_day_stem, _, next_day_cycle = self.ganzhi_day(next_day)
            base_day_stem = next_day_stem
        
        # Calculate hour stem using Wu Shu Dun rule
        hour_stem_char = self._calculate_hour_stem(base_day_stem, hour_branch_index)
        
        # Calculate hour cycle
        stem_index = next((i for i, (char, _, _, _) in enumerate(HEAVENLY_STEMS) if char == hour_stem_char), 0)
        hour_cycle = (stem_index * 12 + hour_branch_index - 1) % 60 + 1
        
        return hour_stem_char, hour_branch_char, hour_cycle
    
    def _get_stem_branch(self, cycle_number: int) -> Tuple[str, str, int, int]:
        """Get Heavenly Stem and Earthly Branch for a given cycle number."""
        stem_index = (cycle_number - 1) % 10
        branch_index = (cycle_number - 1) % 12
        
        stem_char = HEAVENLY_STEMS[stem_index][0]
        branch_char = EARTHLY_BRANCHES[branch_index][0]
        
        return stem_char, branch_char, stem_index + 1, branch_index + 1
    
    def _get_hour_branch(self, hour: int, minute: int = 0) -> Tuple[str, str, int]:
        """Get the Earthly Branch for a given hour."""
        decimal_hour = hour + minute / 60.0
        
        # Handle the special case where 23:00-01:00 is 子 (Zi)
        if decimal_hour >= 23.0 or decimal_hour < 1.0:
            branch_index = 0  # 子 (Zi)
        else:
            # For other hours, calculate normally
            branch_index = int((decimal_hour - 1.0) // 2.0) + 1
            if branch_index >= 12:
                branch_index = 11
        
        branch_char = EARTHLY_BRANCHES[branch_index][0]
        branch_name = EARTHLY_BRANCHES[branch_index][2]
        
        return branch_char, branch_name, branch_index + 1
    
    def _calculate_hour_stem(self, day_stem: str, hour_branch_index: int) -> str:
        """Calculate hour stem using Wu Shu Dun (五鼠遁) rule."""
        # Wu Shu Dun mapping: day stem -> Zi hour stem
        wu_shu_dun = {
            '甲': 0, '己': 0,  # Jiazi starts with 甲
            '乙': 2, '庚': 2,  # Bingzi starts with 丙
            '丙': 4, '辛': 4,  # Wuzi starts with 戊
            '丁': 6, '壬': 6,  # Gengzi starts with 庚
            '戊': 8, '癸': 8   # Renzi starts with 壬
        }
        
        zi_hour_stem_index = wu_shu_dun.get(day_stem, 0)
        hour_stem_index = (zi_hour_stem_index + hour_branch_index - 1) % 10
        
        return HEAVENLY_STEMS[hour_stem_index][0]
    
    def _calculate_cycle_from_stem_branch(self, stem_idx: int, branch_idx: int) -> int:
        """Calculate 60-cycle position from stem and branch indices."""
        # Convert to 0-based indices
        stem_0 = stem_idx - 1
        branch_0 = branch_idx - 1
        
        # Find the cycle position where stem and branch align
        for cycle in range(1, 61):
            cycle_stem = (cycle - 1) % 10
            cycle_branch = (cycle - 1) % 12
            if cycle_stem == stem_0 and cycle_branch == branch_0:
                return cycle
        
        # Fallback (should not happen with valid inputs)
        return 1


class LunarMonthResolver:
    """Resolves target month information from periods."""
    
    def __init__(self, timezone_service: TimezoneService):
        self.logger = setup_logging()
        self.tz_service = timezone_service
    
    def find_period_for_datetime(self, periods: List[MonthPeriod], target_utc: datetime) -> MonthPeriod:
        """Match by CST date-only boundaries: startCstDate <= targetCstDate < endCstDate."""
        # Ensure timezone-naive datetime for CST conversion
        if target_utc.tzinfo is not None:
            target_naive = target_utc.replace(tzinfo=None)
        else:
            target_naive = target_utc
            
        target_cst_date = self.tz_service.utc_to_cst_date(target_naive)
        
        for period in periods:
            if period.start_cst_date <= target_cst_date < period.end_cst_date:
                return period
        
        raise ValueError(f"No period found for date {target_cst_date}")
    
    def calculate_lunar_day(self, target_utc: datetime, period: MonthPeriod) -> int:
        """Return day-in-month using CST date-only difference from period.startCstDate, bounded 1..30."""
        # Ensure timezone-naive datetime for CST conversion
        if target_utc.tzinfo is not None:
            target_naive = target_utc.replace(tzinfo=None)
        else:
            target_naive = target_utc
            
        target_cst_date = self.tz_service.utc_to_cst_date(target_naive)
        days_diff = (target_cst_date - period.start_cst_date).days + 1
        return max(1, min(30, days_diff))
    
    def calculate_lunar_year(self, target_period: MonthPeriod, anchor_solstice_utc: datetime) -> int:
        """Calculate the correct lunar year based on the target period and anchor solstice.
        
        The lunar year follows this logic:
        - Month 1 (Lunar New Year) starts a new lunar year
        - The lunar year number is the Gregorian year when Month 1 occurs
        - Months 11-12 belong to the lunar year that will start with the next Month 1
        - Months 1-10 belong to the lunar year that started with the current Month 1
        """
        # Ensure timezone-naive comparison
        period_start = target_period.start_utc.replace(tzinfo=None) if target_period.start_utc.tzinfo else target_period.start_utc
        anchor_naive = anchor_solstice_utc.replace(tzinfo=None) if anchor_solstice_utc.tzinfo else anchor_solstice_utc
        
        if target_period.month_number == 1:
            # Month 1 (Lunar New Year) - the lunar year is the Gregorian year when this month occurs
            return period_start.year
        elif target_period.month_number in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
            # Months 2-10 - belong to the same lunar year as Month 1 that preceded them
            return period_start.year
        else:  # months 11, 12
            # Months 11-12 - belong to the lunar year that will start with the next Month 1
            # The next Month 1 typically occurs in the next Gregorian year
            return period_start.year + 1


class ResultAssembler:
    """Assembles the final LunisolarDateDTO."""
    
    def __init__(self):
        self.logger = setup_logging()
    
    def assemble_result(
        self,
        lunar_year: int,
        target_period: MonthPeriod,
        lunar_day: int,
        local_hour: int,
        year_ganzhi: Tuple[str, str, int],
        month_ganzhi: Tuple[str, str, int],
        day_ganzhi: Tuple[str, str, int],
        hour_ganzhi: Tuple[str, str, int]
    ) -> LunisolarDateDTO:
        """Assemble complete LunisolarDateDTO from components."""
        
        year_stem, year_branch, year_cycle = year_ganzhi
        month_stem, month_branch, month_cycle = month_ganzhi
        day_stem, day_branch, day_cycle = day_ganzhi
        hour_stem, hour_branch, hour_cycle = hour_ganzhi
        
        return LunisolarDateDTO(
            year=lunar_year,
            month=target_period.month_number,
            day=lunar_day,
            hour=local_hour,
            is_leap_month=target_period.is_leap,
            year_stem=year_stem,
            year_branch=year_branch,
            month_stem=month_stem,
            month_branch=month_branch,
            day_stem=day_stem,
            day_branch=day_branch,
            hour_stem=hour_stem,
            hour_branch=hour_branch,
            year_cycle=year_cycle,
            month_cycle=month_cycle,
            day_cycle=day_cycle,
            hour_cycle=hour_cycle
        )


def solar_to_lunisolar(
    solar_date: str,
    solar_time: str = "12:00",
    timezone_handler: Optional[TimezoneHandler] = None
) -> LunisolarDateDTO:
    """
    Convert solar date and time to lunisolar date with stems and branches.
    
    This is the main entry point that orchestrates the entire conversion pipeline
    following the blueprint architecture.
    
    Args:
        solar_date: Solar date in YYYY-MM-DD format
        solar_time: Solar time in HH:MM format (default: 12:00)
        timezone_handler: TimezoneHandler for timezone conversions (default: CST)
        
    Returns:
        LunisolarDateDTO object with complete lunisolar information
    """
    logger = setup_logging()
    
    try:
        # Initialize services
        tz_service = TimezoneService(timezone_handler)
        window_planner = WindowPlanner()
        ephemeris_service = EphemerisService()
        month_builder = MonthBuilder(tz_service)
        term_indexer = TermIndexer()
        leap_assigner = LeapMonthAssigner()
        sexagenary_engine = SexagenaryEngine(tz_service)
        month_resolver = LunarMonthResolver(tz_service)
        result_assembler = ResultAssembler()
        
        # Parse input and convert to UTC
        local_datetime = tz_service.parse_local_datetime(solar_date, solar_time)
        target_utc = tz_service.local_to_utc(local_datetime)
        
        logger.info(f"Converting {solar_date} {solar_time} to lunisolar")
        
        # Plan calculation window
        window_start, window_end = window_planner.compute_window(target_utc)
        
        # Get ephemeris data
        new_moons = ephemeris_service.compute_new_moons(window_start, window_end)
        principal_terms = ephemeris_service.compute_principal_terms(window_start, window_end)
        
        if not new_moons:
            raise ValueError("No new moons found in calculation window")
        
        # Build month periods and map terms
        periods = month_builder.build_month_periods(new_moons)
        term_indexer.tag_principal_terms(periods, principal_terms)
        
        # Find Winter Solstice for anchor - use the correct one based on target date
        target_naive = target_utc.replace(tzinfo=None) if target_utc.tzinfo else target_utc
        current_year_solstice = window_planner._find_winter_solstice(target_utc.year)
        
        if target_naive >= current_year_solstice:
            anchor_solstice = current_year_solstice
        else:
            anchor_solstice = window_planner._find_winter_solstice(target_utc.year - 1)
        
        # Assign month numbers and leap status
        leap_assigner.assign_month_numbers(periods, anchor_solstice)
        
        # Find target month period
        target_period = month_resolver.find_period_for_datetime(periods, target_utc)
        lunar_day = month_resolver.calculate_lunar_day(target_utc, target_period)
        
        # Calculate lunar year based on month periods and their numbering
        lunar_year = month_resolver.calculate_lunar_year(target_period, anchor_solstice)
        
        # Calculate sexagenary cycles
        year_ganzhi = sexagenary_engine.ganzhi_year(lunar_year)
        
        # Calculate month ganzhi using traditional rules
        month_ganzhi = sexagenary_engine.ganzhi_month(lunar_year, target_period.month_number)
        
        day_ganzhi = sexagenary_engine.ganzhi_day(local_datetime)
        hour_ganzhi = sexagenary_engine.ganzhi_hour(local_datetime, day_ganzhi[0])
        
        # Assemble final result
        result = result_assembler.assemble_result(
            lunar_year=lunar_year,
            target_period=target_period,
            lunar_day=lunar_day,
            local_hour=local_datetime.hour,
            year_ganzhi=year_ganzhi,
            month_ganzhi=month_ganzhi,
            day_ganzhi=day_ganzhi,
            hour_ganzhi=hour_ganzhi
        )
        
        logger.info(f"Conversion completed: {result.year}-{result.month}-{result.day}")
        return result
        
    except Exception as e:
        logger.error(f"Error in solar_to_lunisolar conversion: {e}")
        raise


def get_stem_pinyin(stem_char: str) -> str:
    """Get pinyin for a heavenly stem character."""
    for char, pinyin, _, _ in HEAVENLY_STEMS:
        if char == stem_char:
            return pinyin
    return ""


def get_branch_pinyin(branch_char: str) -> str:
    """Get pinyin for an earthly branch character."""
    for char, pinyin, *_ in EARTHLY_BRANCHES:
        if char == branch_char:
            return pinyin
    return ""


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Lunisolar Calendar Conversion v2')
    parser.add_argument('--date', type=str, required=True, help='Solar date in YYYY-MM-DD format')
    parser.add_argument('--time', type=str, default='12:00', help='Solar time in HH:MM format')
    
    args = parser.parse_args()
    
    try:
        result = solar_to_lunisolar(args.date, args.time)
        
        # Get pinyin for each component
        year_stem_pinyin = get_stem_pinyin(result.year_stem)
        year_branch_pinyin = get_branch_pinyin(result.year_branch)
        month_stem_pinyin = get_stem_pinyin(result.month_stem)
        month_branch_pinyin = get_branch_pinyin(result.month_branch)
        day_stem_pinyin = get_stem_pinyin(result.day_stem)
        day_branch_pinyin = get_branch_pinyin(result.day_branch)
        hour_stem_pinyin = get_stem_pinyin(result.hour_stem)
        hour_branch_pinyin = get_branch_pinyin(result.hour_branch)
        
        print(f"Solar: {args.date} {args.time}")
        print(f"Lunisolar: {result.year}-{result.month}-{result.day} {result.hour}:00")
        print(f"Leap month: {result.is_leap_month}")
        print(f"Year: {result.year_stem}{result.year_branch} ({year_stem_pinyin}{year_branch_pinyin}) [{result.year_cycle}]")
        print(f"Month: {result.month_stem}{result.month_branch} ({month_stem_pinyin}{month_branch_pinyin}) [{result.month_cycle}]")
        print(f"Day: {result.day_stem}{result.day_branch} ({day_stem_pinyin}{day_branch_pinyin}) [{result.day_cycle}]")
        print(f"Hour: {result.hour_stem}{result.hour_branch} ({hour_stem_pinyin}{hour_branch_pinyin}) [{result.hour_cycle}]")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)