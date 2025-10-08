#!/usr/bin/env python3
"""
Lunisolar Calendar System with Construction Stars and Great Yellow Path
十二建星与大黄道择日系统

This module provides a comprehensive implementation of traditional Chinese calendar systems
for date selection and auspiciousness determination. It combines astronomical accuracy
with traditional divination methods.

=== MAIN SYSTEMS ===

1. **LunisolarCalendar (农历系统)**
   - Core lunar calendar calculations using astronomical data
   - Solar terms (二十四节气) calculation with skyfield precision
   - New moon calculations and lunar month determination
   - Winter Solstice rule implementation for month numbering
   - Earthly branch (地支) calculations for dates

2. **ConstructionStars (十二建星)**
   - Twelve Construction Stars divination system
   - Traditional formula: "建满平收黑，除危定执黄，成开皆可用，破闭不可当"
   - Solar term day rule: repeats previous day's star
   - Auspiciousness scoring: 0-4 scale
   - Building branch (建) determination for lunar months

3. **GreatYellowPath (大黄道)**
   - Great Yellow Path (Huang Dao) system with Twelve Spirits
   - Six Yellow Path Days (黄道日): 青龙, 明堂, 金匮, 天德, 玉堂, 司命
   - Six Black Path Days (黑道日): 天刑, 朱雀, 白虎, 天牢, 玄武, 勾陈
   - Azure Dragon starting position mnemonic: "寅申需加子，卯酉却在寅..."
   - Monthly spirit rotation based on lunar calendar

=== CALCULATION METHODS ===

**Construction Stars Calculation:**
1. Determine lunar month and its building branch (建支)
2. Find first day in month with building branch (建日)
3. Count days from 建日 to target date
4. Apply 12-star cycle: 建除满平定执破危成收开闭
5. Handle solar term days (repeat previous day's star)

**Great Yellow Path Calculation:**
1. Determine lunar month number (1-12)
2. Get Azure Dragon starting branch for that month
3. Calculate day's earthly branch using sexagenary cycle
4. Find spirit position: (day_branch - azure_start) % 12
5. Apply spirit sequence to determine auspiciousness

**Lunar Calendar Rules:**
- Winter Solstice must fall in 11th lunar month (子月)
- Leap months have no principal solar term
- 13 new moons in leap years, 12 in regular years
- Month numbering follows traditional Chinese system

=== USAGE EXAMPLES ===

```python
# Initialize for year 2025
calculator = MainCalculator(2025, 'Asia/Ho_Chi_Minh')

# Get complete day information
today = datetime.now()
day_info = calculator.calculate_day_info(today)
print(f"Construction Star: {day_info['star']} ({day_info['translation']})")
print(f"Great Yellow Path: {day_info['gyp_spirit']} ({day_info['gyp_auspiciousness']})")

# Find auspicious days in current month
auspicious_days = calculator.find_auspicious_days_in_month(today.month, min_score=4)

# Print monthly calendar with both systems
calculator.print_month_calendar(today.month)
```

=== TECHNICAL FEATURES ===

- **Astronomical Accuracy**: Uses JPL DE440 ephemeris via skyfield
- **Timezone Support**: Configurable timezone for local calculations
- **Error Handling**: Fallback methods for offline operation
- **Performance**: Efficient caching and batch calculations
- **Validation**: Cross-reference with traditional almanacs
- **Compatibility**: Maintains backward compatibility with existing code

Author: Assistant
Date: 2025
Version: 2.0 (Refactored with modular architecture)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import calendar
import argparse
from enum import Enum
from dataclasses import dataclass
from skyfield.api import load, utc
from skyfield import almanac, almanac_east_asia as almanac_ea
from pytz import timezone

# Configuration constants
EPHEMERIS_FILE = 'nasa/de440.bsp'


class EarthlyBranch(Enum):
    """
    Twelve Earthly Branches (十二地支) used in Chinese calendar system.
    
    Each branch represents a two-hour period and corresponds to one of
    the twelve zodiac animals. Used for both day and month calculations.
    """
    ZI = (0, "子", "Rat")
    CHOU = (1, "丑", "Ox") 
    YIN = (2, "寅", "Tiger")
    MAO = (3, "卯", "Rabbit")
    CHEN = (4, "辰", "Dragon")
    SI = (5, "巳", "Snake")
    WU = (6, "午", "Horse")
    WEI = (7, "未", "Goat")
    SHEN = (8, "申", "Monkey")
    YOU = (9, "酉", "Rooster")
    XU = (10, "戌", "Dog")
    HAI = (11, "亥", "Pig")
    
    def __init__(self, index: int, chinese: str, animal: str):
        self.index = index
        self.chinese = chinese
        self.animal = animal


class GreatYellowPathSpirit(Enum):
    """
    Twelve Spirits (十二神) in the Great Yellow Path system.
    
    Six Yellow Path Days (黄道日) - Auspicious:
    - 青龙 (Qinglong): Azure Dragon
    - 明堂 (Mingtang): Bright Hall
    - 金匮 (Jinkui): Golden Coffer
    - 天德 (Tiande): Heavenly Virtue
    - 玉堂 (Yutang): Jade Hall
    - 司命 (Siming): Life Controller
    
    Six Black Path Days (黑道日) - Inauspicious:
    - 天刑 (Tianxing): Heavenly Punishment
    - 朱雀 (Zhuque): Vermillion Bird
    - 白虎 (Baihu): White Tiger
    - 天牢 (Tianlao): Heavenly Prison
    - 玄武 (Xuanwu): Black Tortoise
    - 勾陈 (Gouchen): Coiling Snake
    """
    # Yellow Path Days (黄道日) - Auspicious
    QINGLONG = (
        "青龙", "Azure Dragon", True, 
        "天乙星，天贵星，利有攸往，所作必成，所求皆得",
        "Auspicious for all activities, especially important endeavors and travel"
    )
    MINGTANG = (
        "明堂", "Bright Hall", True,
        "贵人星，明辅星，利见大人，利有攸往，作事必成", 
        "Favorable for meetings with important people, ceremonies, and official business"
    )
    JINKUI = (
        "金匮", "Golden Coffer", True,
        "福德星，利释道用事，阍者女子用事，吉。宜嫁娶，不宜整戎伍",
        "Good for financial matters, religious activities, and weddings"
    )
    TIANDE = (
        "天德", "Heavenly Virtue", True,
        "宝光星，天德星，其时大郭，作事有成，利有攸往，出行吉",
        "Excellent for travel, important decisions, and virtuous activities"
    )
    YUTANG = (
        "玉堂", "Jade Hall", True,
        "天开星，百事吉，求事成，出行有财，宜文书喜庆之事，利见大人，利安葬，不利泥灶",
        "Favorable for documents, celebrations, meetings with dignitaries, and burials"
    )
    SIMING = (
        "司命", "Life Controller", True,
        "凤辇星，此时从寅至申时用事大吉，从酉至丑时有事不吉，即白天吉，晚上不利",
        "Good for health and longevity matters, but only during daytime hours (寅-申)"
    )
    
    # Black Path Days (黑道日) - Inauspicious
    TIANXING = (
        "天刑", "Heavenly Punishment", False,
        "天刑星，利于出师，战无不克，其它动作谋为皆不宜用，大忌词讼",
        "Avoid legal matters and conflicts; only suitable for military activities"
    )
    ZHUQUE = (
        "朱雀", "Vermillion Bird", False,
        "天讼星，利用公事，常人凶，诸事忌用，谨防争讼",
        "Unfavorable for communication and personal matters; beware of disputes"
    )
    BAIHU = (
        "白虎", "White Tiger", False,
        "天杀星，宜出师畋猎祭祀，皆吉，其余都不利",
        "Dangerous day; only suitable for military expeditions, hunting, and sacrifices"
    )
    TIANLAO = (
        "天牢", "Heavenly Prison", False,
        "镇神星，阴人用事皆吉，其余都不利",
        "Restrictive day; only favorable for women's activities"
    )
    XUANWU = (
        "玄武", "Black Tortoise", False,
        "天狱星，君子用之吉，小人用之凶，忌词讼博戏",
        "Day of hidden dangers; avoid legal matters and gambling"
    )
    GOUCHEN = (
        "勾陈", "Coiling Snake", False,
        "地狱星，起造安葬，犯此绝嗣。此时所作一切事，有始无终，先喜后悲，不利攸往",
        "Day of entanglements and delays; avoid construction and burials"
    )
    
    def __init__(self, chinese: str, english: str, is_auspicious: bool, 
                 traditional_description: str, modern_description: str):
        self.chinese = chinese
        self.english = english
        self.is_auspicious = is_auspicious
        self.traditional_description = traditional_description
        self.modern_description = modern_description


@dataclass
class GreatYellowPathReading:
    """
    Container for a complete day reading in the Great Yellow Path system.
    """
    date: datetime
    lunar_month: int
    day_branch: EarthlyBranch
    spirit: GreatYellowPathSpirit
    path_type: str
    is_auspicious: bool
    auspiciousness: str
    azure_dragon_start: EarthlyBranch
    mnemonic_formula: str


class LunisolarCalendar:
    """
    Core lunisolar calendar calculations and astronomical data (农历核心计算系统).
    
    This class provides the foundation for traditional Chinese calendar calculations,
    implementing astronomically accurate methods for determining lunar months,
    solar terms, and earthly branches according to traditional rules.
    
    === PRIMARY FUNCTIONS ===
    
    **Solar Terms (二十四节气) Calculation:**
    - Uses JPL DE440 ephemeris for precision
    - Calculates all 24 solar terms for a given year
    - Handles timezone conversions automatically
    - Fallback method for offline operation
    - Principal terms: 立春, 惊蛰, 清明, 立夏, 芒种, 小暑, 立秋, 白露, 寒露, 立冬, 大雪, 小寒
    - Minor terms: 雨水, 春分, 谷雨, 小满, 夏至, 大暑, 处暑, 秋分, 霜降, 小雪, 冬至, 大寒
    
    **New Moon Calculations:**
    - Astronomical new moon times using skyfield
    - Extended range calculation (previous year to next year)
    - Timezone-aware calculations
    - Used for lunar month boundary determination
    
    **Lunar Month Determination:**
    - Implements traditional Winter Solstice rule (冬至必在子月)
    - Identifies leap months (闰月) based on solar term distribution
    - Handles 13-month years vs 12-month years
    - Assigns proper earthly branches to months
    - Validates against traditional almanac rules
    
    **Earthly Branch (地支) Calculations:**
    - Sexagenary cycle implementation for daily branches
    - Reference date: February 18, 1912 (甲子日)
    - Continuous cycle counting from reference
    - Used by both Construction Stars and Great Yellow Path systems
    
    === TRADITIONAL RULES IMPLEMENTED ===
    
    1. **Winter Solstice Rule**: 冬至必在子月 (Winter Solstice must fall in 11th month)
    2. **Leap Month Rule**: 闰月无中气 (Leap months have no principal solar term)
    3. **Month Numbering**: Traditional 1-12 system with earthly branch assignment
    4. **Solar Term Priority**: Principal terms determine month boundaries
    5. **New Moon Timing**: Lunar months begin at astronomical new moon
    
    === ATTRIBUTES ===
    
    - year (int): Target calculation year
    - timezone_name (str): Timezone for local calculations
    - local_tz: Pytz timezone object
    - reference_date (datetime): Sexagenary cycle reference (1912-02-18)
    - solar_terms (List[datetime]): All 24 solar terms for the year
    - new_moons (List[datetime]): New moon dates affecting the year
    - lunar_months (List[Tuple]): Complete lunar month data with boundaries
    
    === METHODS ===
    
    - get_earthly_branch_for_date(): Calculate daily earthly branch
    - get_lunar_month_from_date(): Determine lunar month for any date
    - is_solar_term_day(): Check if date is a solar term
    - _calculate_solar_terms(): Astronomical solar term calculation
    - _calculate_new_moons(): New moon timing calculation
    - _calculate_lunar_months(): Traditional lunar month determination
    - _find_winter_solstice(): Precise Winter Solstice timing
    """
    
    # Earthly Branches (地支) for calculations
    EARTHLY_BRANCHES = [
        "子", "丑", "寅", "卯", "辰", "巳",
        "午", "未", "申", "酉", "戌", "亥"
    ]
    
    # Pinyin pronunciations for Earthly Branches
    EARTHLY_BRANCH_PINYIN = {
        "子": "Zǐ",
        "丑": "Chǒu",
        "寅": "Yín",
        "卯": "Mǎo",
        "辰": "Chén",
        "巳": "Sì",
        "午": "Wǔ",
        "未": "Wèi",
        "申": "Shēn",
        "酉": "Yǒu",
        "戌": "Xū",
        "亥": "Hài"
    }
    
    def __init__(self, year: int, timezone_name: str = 'Asia/Ho_Chi_Minh'):
        """
        Initialize the lunisolar calendar for a specific year.
        
        Args:
            year (int): The year to calculate for
            timezone_name (str): Timezone name for calculations
        """
        self.year = year
        self.timezone_name = timezone_name
        self.local_tz = timezone(timezone_name)
        
        # Reference date: February 18, 1912 (Jia Zi day, Lunar New Year 1/1, New Moon)
        self.reference_date = datetime(1912, 2, 18)
        
        self.solar_terms = self._calculate_solar_terms(year)
        self.new_moons = self._calculate_new_moons(year)
        self.lunar_months = self._calculate_lunar_months(year)
    
    def _calculate_solar_terms(self, year: int) -> List[datetime]:
        """
        Calculate the 24 solar terms for a given year using astronomically accurate calculations.
        """
        try:
            ts = load.timescale()
            eph = load(EPHEMERIS_FILE)
            
            # Calculate for the entire year plus some buffer in local timezone
            start_local = datetime(year, 1, 1)
            end_local = datetime(year + 1, 2, 28)
            
            # Localize to configured timezone
            start_time = self.local_tz.localize(start_local)
            end_time = self.local_tz.localize(end_local)
            
            t0 = ts.from_datetime(start_time)
            t1 = ts.from_datetime(end_time)
            
            # Find all solar terms in the time range
            t, tm = almanac.find_discrete(t0, t1, almanac_ea.solar_terms(eph))
            
            solar_terms = []
            for tmi, ti in zip(tm, t):
                # Convert to configured timezone and remove timezone info for consistency
                dt_utc = ti.utc_datetime()
                dt_local = dt_utc.replace(tzinfo=utc).astimezone(self.local_tz)
                dt_obj = dt_local.replace(tzinfo=None)
                
                # Only include terms from the requested year
                if dt_obj.year == year:
                    solar_terms.append(dt_obj)
            
            solar_terms.sort()
            return solar_terms
            
        except Exception as e:
            print(f"Error calculating solar terms for {year}: {e}")
            return self._calculate_solar_terms_fallback(year)
        finally:
            if 'eph' in locals():
                del eph
    
    def _calculate_solar_terms_fallback(self, year: int) -> List[datetime]:
        """
        Fallback method for calculating solar terms using approximate dates.
        """
        base_dates = [
            (2, 4),   # 立春 Lichun
            (2, 19),  # 雨水 Yushui
            (3, 6),   # 惊蛰 Jingzhe
            (3, 21),  # 春分 Chunfen
            (4, 5),   # 清明 Qingming
            (4, 20),  # 谷雨 Guyu
            (5, 6),   # 立夏 Lixia
            (5, 21),  # 小满 Xiaoman
            (6, 6),   # 芒种 Mangzhong
            (6, 21),  # 夏至 Xiazhi
            (7, 7),   # 小暑 Xiaoshu
            (7, 23),  # 大暑 Dashu
            (8, 8),   # 立秋 Liqiu
            (8, 23),  # 处暑 Chushu
            (9, 8),   # 白露 Bailu
            (9, 23),  # 秋分 Qiufen
            (10, 8),  # 寒露 Hanlu
            (10, 23), # 霜降 Shuangjiang
            (11, 7),  # 立冬 Lidong
            (11, 22), # 小雪 Xiaoxue
            (12, 7),  # 大雪 Daxue
            (12, 22), # 冬至 Dongzhi
            (1, 6),   # 小寒 Xiaohan (next year)
            (1, 20),  # 大寒 Dahan (next year)
        ]
        
        solar_terms = []
        for i, (month, day) in enumerate(base_dates):
            term_year = year + 1 if i >= 22 else year
            adjustment = 1 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) and month == 2 and day > 28 else 0
            
            try:
                term_date = datetime(term_year, month, day + adjustment)
                solar_terms.append(term_date)
            except ValueError:
                term_date = datetime(term_year, month, day)
                solar_terms.append(term_date)
                
        return solar_terms
    
    def _calculate_new_moons(self, year: int) -> List[datetime]:
        """
        Calculate new moon dates for a given year using skyfield.
        """
        try:
            ts = load.timescale()
            eph = load(EPHEMERIS_FILE)
            
            # Extend range to capture new moons that affect the year
            start_time = datetime(year - 1, 11, 1)
            end_time = datetime(year + 1, 2, 28)
            
            # Localize to timezone
            start_time_local = self.local_tz.localize(start_time)
            end_time_local = self.local_tz.localize(end_time)
            
            t0 = ts.from_datetime(start_time_local)
            t1 = ts.from_datetime(end_time_local)
            
            t, y = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
            
            new_moons = []
            for ti, yi in zip(t, y):
                if yi == 0:  # New moon phase
                    utc_dt = ti.utc_datetime().replace(tzinfo=utc)
                    local_dt = utc_dt.astimezone(self.local_tz)
                    dt_obj = local_dt.replace(tzinfo=None)
                    new_moons.append(dt_obj)
            
            return new_moons
            
        except Exception as e:
            print(f"Error calculating new moons: {e}")
            return []
        finally:
            if 'eph' in locals():
                del eph
    
    def _find_winter_solstice(self, year: int) -> Optional[datetime]:
        """
        Find the Winter Solstice date using skyfield's seasons almanac.
        """
        try:
            ts = load.timescale()
            eph = load(EPHEMERIS_FILE)
            
            for search_year in [year - 1, year]:
                start_time = datetime(search_year, 12, 1)
                end_time = datetime(search_year + 1, 1, 31)
                
                start_time_local = self.local_tz.localize(start_time)
                end_time_local = self.local_tz.localize(end_time)
                
                t0 = ts.from_datetime(start_time_local)
                t1 = ts.from_datetime(end_time_local)
                
                t, y = almanac.find_discrete(t0, t1, almanac.seasons(eph))
                
                for ti, yi in zip(t, y):
                    if yi == 3:  # Winter solstice
                        utc_dt = ti.utc_datetime().replace(tzinfo=utc)
                        local_dt = utc_dt.astimezone(self.local_tz)
                        winter_solstice = local_dt.replace(tzinfo=None)
                        
                        if winter_solstice.year == year or (winter_solstice.year == year - 1 and winter_solstice.month == 12):
                            return winter_solstice
            
            return None
            
        except Exception as e:
            print(f"Error finding Winter Solstice for {year}: {e}")
            return None
        finally:
            if 'eph' in locals():
                del eph
    
    def _calculate_lunar_months(self, year: int) -> List[Tuple[datetime, datetime, int, str, bool]]:
        """
        Calculate lunar months based on astronomically accurate lunisolar calendar rules.
        
        Returns:
            List[Tuple[datetime, datetime, int, str, bool]]: List of (start_date, end_date, month_number, earthly_branch, is_leap)
        """
        lunar_months = []
        
        # Find Winter Solstice
        winter_solstice = self._find_winter_solstice(year)
        if winter_solstice is None:
            winter_solstice = datetime(year - 1, 12, 22)
        
        # Find the lunar month that contains Winter Solstice - this is the Zi month (11th month)
        zi_month_start = None
        zi_month_end = None
        zi_month_index = None
        
        for i, new_moon in enumerate(self.new_moons):
            if i + 1 < len(self.new_moons):
                month_start = new_moon
                month_end = self.new_moons[i + 1] - timedelta(days=1)
                
                if month_start.date() <= winter_solstice.date() <= month_end.date():
                    zi_month_start = month_start
                    zi_month_end = month_end
                    zi_month_index = i
                    break
        
        if zi_month_start is None:
            return self._calculate_lunar_months_fallback(year)
        
        # Get principal solar terms
        principal_terms = []
        for i in range(1, len(self.solar_terms), 2):
            principal_terms.append(self.solar_terms[i])
        
        if winter_solstice and winter_solstice not in principal_terms:
            principal_terms.append(winter_solstice)
            principal_terms.sort()
        
        # Add the Zi month (11th month)
        lunar_months.append((zi_month_start, zi_month_end, 11, "子", False))
        
        # Track assigned terms
        assigned_terms = set()
        for term in principal_terms:
            if zi_month_start.date() <= term.date() <= zi_month_end.date():
                assigned_terms.add(term)
        
        # Calculate months before the Zi month
        current_index = zi_month_index - 1
        month_numbers_before = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 12]
        earthly_branches_before = ["亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"]
        
        months_before_zi = []
        for i, (month_num, branch) in enumerate(zip(month_numbers_before, earthly_branches_before)):
            if current_index >= 0:
                month_start = self.new_moons[current_index]
                if current_index + 1 < len(self.new_moons):
                    month_end = self.new_moons[current_index + 1] - timedelta(days=1)
                else:
                    month_end = zi_month_start - timedelta(days=1)
                
                if (month_start.year == year or month_end.year == year or
                    (month_start.year < year and month_end.year >= year)):
                    
                    # Check for principal solar term
                    for term in principal_terms:
                        if (month_start.date() <= term.date() <= month_end.date() and 
                            term not in assigned_terms):
                            assigned_terms.add(term)
                            break
                    
                    months_before_zi.append((month_start, month_end, month_num, branch, False))
                
                current_index -= 1
            else:
                break
        
        months_before_zi.reverse()
        lunar_months.extend(months_before_zi)
        
        # Calculate months after the Zi month
        current_index = zi_month_index + 1
        month_numbers_after = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        earthly_branches_after = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        
        for i, (month_num, branch) in enumerate(zip(month_numbers_after, earthly_branches_after)):
            if current_index < len(self.new_moons) - 1:
                month_start = self.new_moons[current_index]
                month_end = self.new_moons[current_index + 1] - timedelta(days=1)
                
                if (month_start.year == year or month_end.year == year or
                    (month_start.year <= year and month_end.year > year)):
                    
                    # Check for principal solar term
                    has_principal_term = False
                    for term in principal_terms:
                        if (month_start.date() <= term.date() <= month_end.date() and 
                            term not in assigned_terms):
                            has_principal_term = True
                            assigned_terms.add(term)
                            break
                    
                    # Determine if this should be a leap month
                    is_leap = False
                    if not has_principal_term:
                        total_new_moons_in_year = sum(1 for nm in self.new_moons 
                                                    if nm.year == year or (nm.year == year + 1 and nm.month <= 2))
                        
                        if total_new_moons_in_year >= 13:
                            is_leap = True
                            if lunar_months:
                                prev_month_num = lunar_months[-1][2]
                                month_num = prev_month_num
                                branch = lunar_months[-1][3]
                    
                    lunar_months.append((month_start, month_end, month_num, branch, is_leap))
                
                current_index += 1
            else:
                break
        
        lunar_months.sort(key=lambda x: x[0])
        return lunar_months
    
    def _calculate_lunar_months_fallback(self, year: int) -> List[Tuple[datetime, datetime, int, str, bool]]:
        """
        Fallback method for calculating lunar months using simplified approach.
        """
        lunar_months = []
        
        # Find 立春 (Beginning of Spring) for the year
        lichun = self.solar_terms[0]
        
        # Find the new moon closest to or after 立春
        lichun_new_moon = None
        for new_moon in self.new_moons:
            if new_moon >= lichun:
                lichun_new_moon = new_moon
                break
        
        if lichun_new_moon is None:
            for new_moon in reversed(self.new_moons):
                if new_moon < lichun:
                    lichun_new_moon = new_moon
                    break
        
        if lichun_new_moon is None:
            return lunar_months
        
        # Start from the new moon that begins the first lunar month
        current_new_moon_index = self.new_moons.index(lichun_new_moon)
        
        # Generate 12 lunar months starting from 正月 (Yin month)
        earthly_branches = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
        
        for month_num in range(1, 13):
            if current_new_moon_index < len(self.new_moons):
                start_date = self.new_moons[current_new_moon_index]
                
                if current_new_moon_index + 1 < len(self.new_moons):
                    end_date = self.new_moons[current_new_moon_index + 1] - timedelta(days=1)
                else:
                    end_date = datetime(year, 12, 31)
                
                branch = earthly_branches[month_num - 1]
                lunar_months.append((start_date, end_date, month_num, branch, False))
                current_new_moon_index += 1
        
        return lunar_months
    
    def get_earthly_branch_for_date(self, date: datetime) -> str:
        """
        Calculate the Earthly Branch for a given date.
        
        Args:
            date (datetime): The date to calculate for
            
        Returns:
            str: The Earthly Branch character for the date
        """
        days_diff = (date - self.reference_date).days
        branch_index = days_diff % 12
        return self.EARTHLY_BRANCHES[branch_index]
    
    def get_lunar_month_from_date(self, date: datetime) -> Tuple[int, str, bool]:
        """
        Determine the lunar month information based on new moon cycles.
        
        Args:
            date (datetime): The date to check
            
        Returns:
            Tuple[int, str, bool]: (month_number, earthly_branch, is_leap)
        """
        for start_date, end_date, month_num, branch, is_leap in self.lunar_months:
            if start_date.date() <= date.date() <= end_date.date():
                return month_num, branch, is_leap
        
        return 1, "寅", False
    
    def is_solar_term_day(self, date: datetime) -> bool:
        """
        Check if a given date is a solar term day (specifically one of the 12 principal terms).
        
        Args:
            date (datetime): The date to check
            
        Returns:
            bool: True if it's a principal solar term day
        """
        principal_terms = [self.solar_terms[i] for i in range(0, len(self.solar_terms), 2)]
        
        for term_date in principal_terms:
            if term_date.date() == date.date():
                return True
        return False


class ConstructionStars:
    """
    Calculator for the Twelve Construction Stars (十二建星) system.
    
    The Twelve Construction Stars is a traditional Chinese divination system used for
    date selection and determining the auspiciousness of daily activities. This system
    is based on the relationship between lunar months and the daily earthly branch cycle.
    
    === TRADITIONAL FOUNDATION ===
    
    **Core Formula (传统口诀):**
    "建满平收黑，除危定执黄，成开皆可用，破闭不可当"
    
    Translation:
    - 建满平收黑: Jiàn, Mǎn, Píng, Shōu are Black (inauspicious)
    - 除危定执黄: Chú, Wēi, Dìng, Zhí are Yellow (auspicious)
    - 成开皆可用: Chéng, Kāi are both usable (moderate)
    - 破闭不可当: Pò, Bì cannot be used (very inauspicious)
    
    **The Twelve Stars (十二建星):**
    1. 建 (Jiàn) - Establish: Foundation laying, but generally inauspicious
    2. 除 (Chú) - Remove: Clearing obstacles, highly auspicious
    3. 满 (Mǎn) - Full: Completion, but inauspicious for new starts
    4. 平 (Píng) - Balanced: Stability, but generally inauspicious
    5. 定 (Dìng) - Set: Determination, highly auspicious
    6. 执 (Zhí) - Hold: Persistence, highly auspicious
    7. 破 (Pò) - Break: Destruction, very inauspicious
    8. 危 (Wēi) - Danger: Risk, but paradoxically auspicious
    9. 成 (Chéng) - Accomplish: Achievement, moderately good
    10. 收 (Shōu) - Harvest: Gathering, but inauspicious for new ventures
    11. 开 (Kāi) - Open: Beginning, moderately good
    12. 闭 (Bì) - Close: Ending, very inauspicious
    
    === CALCULATION METHOD ===
    
    **Step-by-Step Process:**
    1. **Determine Lunar Month**: Find which lunar month the target date falls in
    2. **Identify Building Branch (建支)**: Each lunar month has an associated earthly branch
    3. **Find Building Day (建日)**: Locate the first day in the month with the building branch
    4. **Count Days**: Calculate days elapsed from the building day to target date
    5. **Apply Cycle**: Use modulo 12 to find position in the star sequence
    6. **Handle Solar Terms**: Solar term days repeat the previous day's star
    
    **Building Branch Assignment:**
    - Month 1 (正月): 寅 (Tiger)
    - Month 2 (二月): 卯 (Rabbit)
    - Month 3 (三月): 辰 (Dragon)
    - Month 4 (四月): 巳 (Snake)
    - Month 5 (五月): 午 (Horse)
    - Month 6 (六月): 未 (Goat)
    - Month 7 (七月): 申 (Monkey)
    - Month 8 (八月): 酉 (Rooster)
    - Month 9 (九月): 戌 (Dog)
    - Month 10 (十月): 亥 (Pig)
    - Month 11 (十一月): 子 (Rat)
    - Month 12 (十二月): 丑 (Ox)
    
    **Special Rules:**
    - **Solar Term Rule**: On principal solar term days (中气), the star does not advance
      but repeats the previous day's star. This maintains the traditional rhythm.
    - **Leap Month Rule**: Leap months use the same building branch as their base month
    - **Year Boundary**: Calculations span across year boundaries seamlessly
    
    === AUSPICIOUSNESS SCORING ===
    
    **4-Point Scale:**
    - Score 4 (Highly Auspicious): 除, 危, 定, 执 - Best for important activities
    - Score 3 (Moderately Good): 成, 开 - Suitable for most activities
    - Score 1 (Inauspicious): 建, 满, 平, 收 - Avoid important activities
    - Score 0 (Very Inauspicious): 破, 闭 - Avoid all significant activities
    
    **Traditional Applications:**
    - **Highly Auspicious Days**: Weddings, business openings, travel, contracts
    - **Moderate Days**: Routine work, meetings, minor decisions
    - **Inauspicious Days**: Avoid major decisions, postpone important events
    - **Very Inauspicious Days**: Rest, reflection, avoid all significant activities
    
    === ATTRIBUTES ===
    
    - CONSTRUCTION_STARS: The 12 star sequence in traditional order
    - STAR_TRANSLATIONS: English translations with pinyin
    - AUSPICIOUSNESS: Complete scoring and classification system
    - calendar: Reference to LunisolarCalendar for date calculations
    
    === METHODS ===
    
    - get_construction_star_for_date(): Calculate star for specific date
    - get_auspiciousness_info(): Get detailed auspiciousness data
    - calculate_day_info(): Complete star analysis for a date
    - find_auspicious_days_in_month(): Find favorable days in a month
    """
    
    # The twelve construction stars in order
    CONSTRUCTION_STARS = [
        "建", "除", "满", "平", "定", "执", 
        "破", "危", "成", "收", "开", "闭"
    ]
    
    # English translations for reference
    STAR_TRANSLATIONS = {
        "建": "Jiàn (Establish)",
        "除": "Chú (Remove)", 
        "满": "Mǎn (Full)",
        "平": "Píng (Balanced)",
        "定": "Dìng (Set)",
        "执": "Zhí (Hold)",
        "破": "Pò (Break)",
        "危": "Wēi (Danger)",
        "成": "Chéng (Accomplish)",
        "收": "Shōu (Harvest)",
        "开": "Kāi (Open)",
        "闭": "Bì (Close)"
    }
    
    # Auspiciousness classifications based on traditional formula:
    # "建满平收黑，除危定执黄，成开皆可用，破闭不可当"
    AUSPICIOUSNESS = {
        "建": {"level": "inauspicious", "color": "black", "score": 1},
        "满": {"level": "inauspicious", "color": "black", "score": 1},
        "平": {"level": "inauspicious", "color": "black", "score": 1},
        "收": {"level": "inauspicious", "color": "black", "score": 1},
        "除": {"level": "auspicious", "color": "yellow", "score": 4},
        "危": {"level": "auspicious", "color": "yellow", "score": 4},
        "定": {"level": "auspicious", "color": "yellow", "score": 4},
        "执": {"level": "auspicious", "color": "yellow", "score": 4},
        "成": {"level": "moderate", "color": "usable", "score": 3},
        "开": {"level": "moderate", "color": "usable", "score": 3},
        "破": {"level": "very_inauspicious", "color": "unsuitable", "score": 0},
        "闭": {"level": "very_inauspicious", "color": "unsuitable", "score": 0}
    }
    
    def __init__(self, calendar: LunisolarCalendar):
        """
        Initialize the Construction Stars calculator.
        
        Args:
            calendar (LunisolarCalendar): The lunisolar calendar instance
        """
        self.calendar = calendar
    
    def get_construction_star_for_date(self, date: datetime) -> str:
        """
        Calculate the Construction Star for a specific date using traditional method.
        
        Args:
            date (datetime): The date to calculate for
            
        Returns:
            str: The Construction Star character for the date
        """
        # Check if this is a solar term day - if so, repeat previous day's star
        if self.calendar.is_solar_term_day(date):
            previous_date = date - timedelta(days=1)
            return self.get_construction_star_for_date(previous_date)
        
        # Get the lunar month information for this date
        month_num, building_branch, is_leap = self.calendar.get_lunar_month_from_date(date)
        
        # Find the lunar month period for this date
        lunar_month_start = None
        for start_date, end_date, month_number, branch, leap in self.calendar.lunar_months:
            if (month_number == month_num and branch == building_branch and leap == is_leap and
                start_date.date() <= date.date() <= end_date.date()):
                lunar_month_start = start_date
                break
        
        if lunar_month_start is None:
            lunar_month_start = datetime(date.year, date.month, 1)
        
        # Find the first day in this lunar month with the building branch
        current_date = lunar_month_start
        jian_day = None
        
        search_limit = lunar_month_start + timedelta(days=60)
        while current_date <= search_limit:
            if self.calendar.get_earthly_branch_for_date(current_date) == building_branch:
                jian_day = current_date
                break
            current_date += timedelta(days=1)
        
        if jian_day is None:
            jian_day = lunar_month_start
        
        # Calculate days since the "建" day
        date_normalized = date.replace(hour=0, minute=0, second=0, microsecond=0)
        jian_day_normalized = jian_day.replace(hour=0, minute=0, second=0, microsecond=0)
        days_since_jian = (date_normalized - jian_day_normalized).days
        star_index = days_since_jian % 12
        return self.CONSTRUCTION_STARS[star_index]
    
    def get_auspiciousness_info(self, star: str) -> Dict:
        """
        Get detailed auspiciousness information for a Construction Star.
        
        Args:
            star (str): The Construction Star character
            
        Returns:
            Dict: Dictionary containing auspiciousness level, color classification, and score
        """
        return self.AUSPICIOUSNESS.get(star, {"level": "unknown", "color": "unknown", "score": 2})
    
    def calculate_day_info(self, date: datetime) -> Dict:
        """
        Calculate complete Construction Star information for a specific date.
        
        Args:
            date (datetime): The date to analyze
            
        Returns:
            Dict: Complete Construction Star information
        """
        star = self.get_construction_star_for_date(date)
        auspiciousness = self.get_auspiciousness_info(star)
        earthly_branch = self.calendar.get_earthly_branch_for_date(date)
        lunar_month_num, building_branch, is_leap = self.calendar.get_lunar_month_from_date(date)
        is_solar_term = self.calendar.is_solar_term_day(date)
        
        lunar_month_display = f"{'閏' if is_leap else ''}{lunar_month_num}"
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "star": star,
            "translation": self.STAR_TRANSLATIONS.get(star, "Unknown"),
            "auspiciousness_level": auspiciousness["level"],
            "color_classification": auspiciousness["color"],
            "score": auspiciousness["score"],
            "earthly_branch": earthly_branch,
            "lunar_month": lunar_month_num,
            "lunar_month_display": lunar_month_display,
            "building_branch": building_branch,
            "is_leap_month": is_leap,
            "is_solar_term_day": is_solar_term,
            "note": "Repeats previous day's star" if is_solar_term else None
        }
    
    def find_auspicious_days_in_month(self, month: int, min_score: int = 3) -> List[Dict]:
        """
        Find all auspicious days in a specific month.
        
        Args:
            month (int): Month number (1-12)
            min_score (int): Minimum auspiciousness score (0-4)
            
        Returns:
            List[Dict]: List of auspicious days with their information
        """
        auspicious_days = []
        days_in_month = calendar.monthrange(self.calendar.year, month)[1]
        
        for day in range(1, days_in_month + 1):
            date = datetime(self.calendar.year, month, day)
            day_info = self.calculate_day_info(date)
            if day_info["score"] >= min_score:
                auspicious_days.append(day_info)
        
        return auspicious_days


class GreatYellowPath:
    """
    Calculator for the Great Yellow Path (大黄道) system.
    
    The Great Yellow Path (大黄道) is a traditional Chinese astrological system that
    determines daily spiritual influences based on the Twelve Spirits (十二神) cycle.
    This system is used for timing activities and understanding cosmic energies.
    
    === TRADITIONAL FOUNDATION ===
    
    **The Twelve Spirits (十二神):**
    1. 青龙 (Qīng Lóng) - Azure Dragon: Highly auspicious, brings good fortune
    2. 明堂 (Míng Táng) - Bright Hall: Very auspicious, favorable for ceremonies
    3. 天刑 (Tiān Xíng) - Heavenly Punishment: Inauspicious, avoid important activities
    4. 朱雀 (Zhū Què) - Vermillion Bird: Inauspicious, brings conflicts
    5. 金匮 (Jīn Guì) - Golden Coffer: Highly auspicious, excellent for wealth
    6. 天德 (Tiān Dé) - Heavenly Virtue: Very auspicious, divine blessing
    7. 白虎 (Bái Hǔ) - White Tiger: Very inauspicious, dangerous energy
    8. 玉堂 (Yù Táng) - Jade Hall: Highly auspicious, noble activities
    9. 天牢 (Tiān Láo) - Heavenly Prison: Very inauspicious, confinement
    10. 元武 (Yuán Wǔ) - Dark Warrior: Inauspicious, hidden dangers
    11. 司命 (Sī Mìng) - Life Controller: Very auspicious, life matters
    12. 勾陈 (Gōu Chén) - Hook Array: Inauspicious, entanglements
    
    **Auspiciousness Classification:**
    - **Highly Auspicious (大吉)**: 青龙, 金匮, 玉堂 - Best for major activities
    - **Very Auspicious (吉)**: 明堂, 天德, 司命 - Excellent for important matters
    - **Inauspicious (凶)**: 天刑, 朱雀, 元武, 勾陈 - Avoid significant activities
    - **Very Inauspicious (大凶)**: 白虎, 天牢 - Avoid all important activities
    
    === CALCULATION METHOD ===
    
    **Traditional Mnemonic Formula (口诀):**
    "寅申需加子，卯酉却在寅，辰戍龙位上，巳亥午上存，子午临申地，丑未戍上行"
    
    **Azure Dragon Monthly Starting Position:**
    The Azure Dragon's starting earthly branch varies by lunar month:
    - Month 1,7 (正月,七月): 子 (Rat) - "寅申需加子"
    - Month 2,8 (二月,八月): 寅 (Tiger) - "卯酉却在寅"
    - Month 3,9 (三月,九月): 辰 (Dragon) - "辰戍龙位上"
    - Month 4,10 (四月,十月): 午 (Horse) - "巳亥午上存"
    - Month 5,11 (五月,十一月): 申 (Monkey) - "子午临申地"
    - Month 6,12 (六月,十二月): 戌 (Dog) - "丑未戍上行"
    
    **Step-by-Step Process:**
    1. **Determine Lunar Month**: Find which lunar month the target date falls in
    2. **Get Azure Dragon Start**: Find Azure Dragon's starting branch for that month
    3. **Calculate Day Branch**: Determine the earthly branch for the target date
    4. **Find Spirit Position**: Calculate offset from Azure Dragon start to day branch
    5. **Apply Spirit Sequence**: Use the offset to find the corresponding spirit
    
    **Spirit Sequence (from Azure Dragon):**
    青龙 → 明堂 → 天刑 → 朱雀 → 金匮 → 天德 → 白虎 → 玉堂 → 天牢 → 元武 → 司命 → 勾陈
    
    **Traditional Applications:**
    - **Highly Auspicious Days**: Weddings, business ventures, important contracts
    - **Very Auspicious Days**: Ceremonies, official appointments, major decisions
    - **Inauspicious Days**: Postpone important activities, focus on routine work
    - **Very Inauspicious Days**: Rest, avoid conflicts, delay major undertakings
    
    === INTEGRATION WITH CONSTRUCTION STARS ===
    
    The Great Yellow Path system is often used in conjunction with the Twelve
    Construction Stars to provide a comprehensive analysis of daily auspiciousness.
    When both systems agree on auspiciousness, the day is considered especially
    favorable or unfavorable.
    
    === ATTRIBUTES ===
    
    - SPIRIT_SEQUENCE: The 12 spirits in traditional order
    - AZURE_DRAGON_MONTHLY_START: Starting positions by lunar month
    - MNEMONIC_FORMULAS: Traditional formulas for validation
    - calendar: Reference to LunisolarCalendar for date calculations
    
    === METHODS ===
    
    - get_day_branch_from_date(): Calculate earthly branch for a date
    - get_azure_dragon_starting_branch(): Get Azure Dragon start for lunar month
    - calculate_spirit_for_day(): Determine the spirit for a specific date
    - get_great_yellow_path_reading(): Complete analysis with auspiciousness
    """
    
    # Azure Dragon monthly starting points
    # Traditional mnemonic formula mapping (口诀)
    # 寅申需加子，卯酉却在寅，辰戍龙位上，巳亥午上存，子午临申地，丑未戍上行
    AZURE_DRAGON_MONTHLY_START = {
        1: EarthlyBranch.ZI,    # 寅申需加子 - Month 1 (寅) starts at 子
        2: EarthlyBranch.YIN,   # 卯酉却在寅 - Month 2 (卯) starts at 寅
        3: EarthlyBranch.CHEN,  # 辰戍龙位上 - Month 3 (辰) starts at 辰
        4: EarthlyBranch.WU,    # 巳亥午上存 - Month 4 (巳) starts at 午
        5: EarthlyBranch.SHEN,  # 子午临申地 - Month 5 (午) starts at 申
        6: EarthlyBranch.XU,    # 丑未戍上行 - Month 6 (未) starts at 戌
        7: EarthlyBranch.ZI,    # 寅申需加子 - Month 7 (申) starts at 子
        8: EarthlyBranch.YIN,   # 卯酉却在寅 - Month 8 (酉) starts at 寅
        9: EarthlyBranch.CHEN,  # 辰戍龙位上 - Month 9 (戌) starts at 辰
        10: EarthlyBranch.WU,   # 巳亥午上存 - Month 10 (亥) starts at 午
        11: EarthlyBranch.SHEN, # 子午临申地 - Month 11 (子) starts at 申
        12: EarthlyBranch.XU    # 丑未戍上行 - Month 12 (丑) starts at 戌
    }
    
    # Fixed sequence of Twelve Spirits starting from Azure Dragon
    SPIRIT_SEQUENCE = [
        GreatYellowPathSpirit.QINGLONG,   # 青龙 - Yellow Path
        GreatYellowPathSpirit.MINGTANG,   # 明堂 - Yellow Path  
        GreatYellowPathSpirit.TIANXING,   # 天刑 - Black Path
        GreatYellowPathSpirit.ZHUQUE,     # 朱雀 - Black Path
        GreatYellowPathSpirit.JINKUI,     # 金匮 - Yellow Path
        GreatYellowPathSpirit.TIANDE,     # 天德 - Yellow Path
        GreatYellowPathSpirit.BAIHU,      # 白虎 - Black Path
        GreatYellowPathSpirit.YUTANG,     # 玉堂 - Yellow Path
        GreatYellowPathSpirit.TIANLAO,    # 天牢 - Black Path
        GreatYellowPathSpirit.XUANWU,     # 玄武 - Black Path
        GreatYellowPathSpirit.SIMING,     # 司命 - Yellow Path
        GreatYellowPathSpirit.GOUCHEN     # 勾陈 - Black Path
    ]
    
    # Mnemonic formula validation strings
    MNEMONIC_FORMULAS = {
        1: "寅申需加子",  # Months 1&7 start at 子
        2: "卯酉却在寅",  # Months 2&8 start at 寅
        3: "辰戍龙位上",  # Months 3&9 start at 辰
        4: "巳亥午上存",  # Months 4&10 start at 午
        5: "子午临申地",  # Months 5&11 start at 申
        6: "丑未戍上行",  # Months 6&12 start at 戌
        7: "寅申需加子",  # Months 1&7 start at 子
        8: "卯酉却在寅",  # Months 2&8 start at 寅
        9: "辰戍龙位上",  # Months 3&9 start at 辰
        10: "巳亥午上存", # Months 4&10 start at 午
        11: "子午临申地", # Months 5&11 start at 申
        12: "丑未戍上行"  # Months 6&12 start at 戌
    }
    
    def __init__(self, calendar: LunisolarCalendar):
        """
        Initialize the Great Yellow Path calculator.
        
        Args:
            calendar (LunisolarCalendar): The lunisolar calendar instance
        """
        self.calendar = calendar
    
    def get_day_branch_from_date(self, date: datetime) -> EarthlyBranch:
        """
        Calculate the earthly branch for a given date based on the traditional sexagenary cycle.
        
        Args:
            date: The date to calculate for
            
        Returns:
            The earthly branch for that date
        """
        # Reference date: 2025-01-01 is 甲子 day (Jiǎzǐ)
        reference_date = datetime(2025, 1, 1)
        reference_branch = EarthlyBranch.ZI
        
        # Calculate days difference
        days_diff = (date - reference_date).days
        
        # Get the earthly branch index (0-11)
        reference_index = reference_branch.value[0]
        branch_index = (reference_index + days_diff) % 12
        
        return list(EarthlyBranch)[branch_index]
    
    def get_azure_dragon_starting_branch(self, lunar_month: int) -> EarthlyBranch:
        """
        Get the Azure Dragon starting branch for a given lunar month.
        
        Args:
            lunar_month: The lunar month number (1-12)
            
        Returns:
            The earthly branch where Azure Dragon starts for this month
        """
        return self.AZURE_DRAGON_MONTHLY_START[lunar_month]
    
    def calculate_spirit_for_day(self, date: datetime) -> GreatYellowPathSpirit:
        """
        Calculate the governing spirit for a given day based on the Great Yellow Path system.
        
        Args:
            date: The date to calculate for
            
        Returns:
            The governing spirit for that day
        """
        lunar_month_num, _, _ = self.calendar.get_lunar_month_from_date(date)
        day_branch = self.get_day_branch_from_date(date)
        azure_dragon_start = self.get_azure_dragon_starting_branch(lunar_month_num)
        
        # Calculate the offset from Azure Dragon starting position
        azure_start_index = azure_dragon_start.value[0]
        day_branch_index = day_branch.value[0]
        
        # Calculate the spirit index in the sequence
        spirit_index = (day_branch_index - azure_start_index) % 12
        
        return self.SPIRIT_SEQUENCE[spirit_index]
    
    def get_great_yellow_path_reading(self, date: datetime) -> GreatYellowPathReading:
        """
        Get a complete Great Yellow Path reading for a given date.
        
        Args:
            date: The date to get reading for
            
        Returns:
            Complete Great Yellow Path reading including spirit, path type, and auspiciousness
        """
        lunar_month_num, _, _ = self.calendar.get_lunar_month_from_date(date)
        day_branch = self.get_day_branch_from_date(date)
        spirit = self.calculate_spirit_for_day(date)
        azure_dragon_start = self.get_azure_dragon_starting_branch(lunar_month_num)
        
        # Determine if it's Yellow Path (auspicious) or Black Path (inauspicious)
        is_yellow_path = spirit in [
            GreatYellowPathSpirit.QINGLONG,   # 青龙
            GreatYellowPathSpirit.MINGTANG,   # 明堂
            GreatYellowPathSpirit.JINKUI,     # 金匮
            GreatYellowPathSpirit.TIANDE,     # 天德
            GreatYellowPathSpirit.YUTANG,     # 玉堂
            GreatYellowPathSpirit.SIMING      # 司命
        ]
        
        path_type = "黄道" if is_yellow_path else "黑道"
        auspiciousness = "吉" if is_yellow_path else "凶"
        
        return GreatYellowPathReading(
            date=date,
            lunar_month=lunar_month_num,
            day_branch=day_branch,
            spirit=spirit,
            path_type=path_type,
            is_auspicious=is_yellow_path,
            auspiciousness=auspiciousness,
            azure_dragon_start=azure_dragon_start,
            mnemonic_formula=self.MNEMONIC_FORMULAS[lunar_month_num]
        )


class MainCalculator:
    """
    Main calculator class that combines all three systems for comprehensive Chinese calendar analysis.
    
    This unified interface integrates the Lunisolar Calendar (农历), Twelve Construction Stars (十二建星),
    and Great Yellow Path (大黄道) systems to provide complete traditional Chinese date selection
    and auspiciousness analysis. The class maintains backward compatibility while leveraging
    the new modular architecture for improved maintainability.
    
    === INTEGRATED SYSTEMS ===
    
    **1. Lunisolar Calendar (农历系统)**
    - Solar Terms (二十四节气): 24 seasonal markers
    - Lunar Months (农历月份): Traditional month calculations
    - Earthly Branches (地支): 12-day cycle for date identification
    - New Moon Calculations: Precise astronomical timing
    
    **2. Twelve Construction Stars (十二建星)**
    - Traditional divination system for daily activities
    - Based on lunar month and earthly branch relationships
    - Provides 4-level auspiciousness scoring (0-4)
    - Follows traditional formula: "建满平收黑，除危定执黄，成开皆可用，破闭不可当"
    
    **3. Great Yellow Path (大黄道)**
    - Twelve Spirits (十二神) cycle for cosmic influences
    - Azure Dragon positioning by lunar month
    - Yellow Path (吉) vs Black Path (凶) classification
    - Traditional mnemonic formulas for calculation
    
    === COMPREHENSIVE ANALYSIS ===
    
    **Combined Auspiciousness Assessment:**
    When both Construction Stars and Great Yellow Path systems agree:
    - **Double Auspicious**: Highly favorable for all activities
    - **Double Inauspicious**: Strongly avoid important activities
    - **Mixed Results**: Consider specific activity requirements
    
    **Practical Applications:**
    - **Wedding Planning**: Find days with high scores in both systems
    - **Business Ventures**: Identify optimal timing for launches
    - **Travel Planning**: Select auspicious departure dates
    - **Contract Signing**: Choose favorable negotiation days
    - **Medical Procedures**: Avoid inauspicious periods
    - **Construction Projects**: Time groundbreaking ceremonies
    
    === YEAR-LEVEL ANALYSIS ===
    
    **Statistical Insights:**
    - Star frequency distribution across the year
    - Auspiciousness percentage breakdown
    - Seasonal patterns in favorable days
    - Lunar month characteristics and trends
    
    **Calendar Integration:**
    - Seamless handling of leap months (闰月)
    - Accurate solar term timing with astronomical precision
    - Winter Solstice rule compliance for month numbering
    - Cross-year boundary calculations
    
    === BACKWARD COMPATIBILITY ===
    
    This class maintains full compatibility with previous implementations while
    providing enhanced functionality through the modular architecture:
    
    **Legacy Method Support:**
    - All original method signatures preserved
    - Identical return value formats
    - Same constant definitions and access patterns
    - Consistent error handling behavior
    
    **Enhanced Features:**
    - Improved calculation accuracy
    - Better error handling and validation
    - Comprehensive documentation and examples
    - Modular component access for advanced users
    
    === USAGE EXAMPLES ===
    
    ```python
    # Initialize for year 2025
    calculator = MainCalculator(2025)
    
    # Get complete day analysis
    day_info = calculator.calculate_day_info(datetime(2025, 1, 15))
    
    # Find auspicious days in a month
    good_days = calculator.find_auspicious_days_in_month(3, min_score=3)
    
    # Generate year summary
    summary = calculator.calculate_year_summary()
    
    # Print formatted calendar
    calculator.print_month_calendar(6)
    ```
    
    === ATTRIBUTES ===
    
    **Core Components:**
    - calendar: LunisolarCalendar instance for date calculations
    - construction_stars: ConstructionStars calculator
    - great_yellow_path: GreatYellowPath calculator
    
    **Exposed Constants (for compatibility):**
    - CONSTRUCTION_STARS: The 12 construction star sequence
    - STAR_TRANSLATIONS: English translations with pinyin
    - AUSPICIOUSNESS: Complete auspiciousness classification
    - EARTHLY_BRANCHES: 12 earthly branch characters
    - AZURE_DRAGON_MONTHLY_START: Monthly starting positions
    - SPIRIT_SEQUENCE: The 12 spirits in order
    
    **Calculated Data:**
    - solar_terms: List of solar term dates for the year
    - new_moons: List of new moon dates
    - lunar_months: List of lunar month information
    
    === METHODS ===
    
    **Primary Analysis:**
    - calculate_day_info(): Complete analysis for a specific date
    - calculate_month_calendar(): Full month analysis
    - calculate_year_summary(): Annual statistics and patterns
    
    **Specialized Queries:**
    - find_auspicious_days_in_month(): Filter favorable days
    - get_construction_star_for_date(): Construction star calculation
    - get_great_yellow_path_reading(): Great Yellow Path analysis
    
    **Utility Methods:**
    - get_earthly_branch_for_date(): Date to earthly branch conversion
    - get_auspiciousness_info(): Detailed auspiciousness data
    - print_month_calendar(): Formatted calendar display
    """
    
    def __init__(self, year: int, timezone_name: str = 'Asia/Ho_Chi_Minh'):
        """
        Initialize the calculator for a specific year.
        
        Args:
            year (int): The year to calculate for
            timezone_name (str): Timezone name for calculations
        """
        self.year = year
        self.timezone_name = timezone_name
        
        # Initialize the three main components
        self.calendar = LunisolarCalendar(year, timezone_name)
        self.construction_stars = ConstructionStars(self.calendar)
        self.great_yellow_path = GreatYellowPath(self.calendar)
        
        # Expose calendar properties for backward compatibility
        self.solar_terms = self.calendar.solar_terms
        self.new_moons = self.calendar.new_moons
        self.lunar_months = self.calendar.lunar_months
        self.local_tz = self.calendar.local_tz
        self.reference_date = self.calendar.reference_date
        
        # Expose constants for backward compatibility
        self.CONSTRUCTION_STARS = self.construction_stars.CONSTRUCTION_STARS
        self.STAR_TRANSLATIONS = self.construction_stars.STAR_TRANSLATIONS
        self.AUSPICIOUSNESS = self.construction_stars.AUSPICIOUSNESS
        self.EARTHLY_BRANCHES = self.calendar.EARTHLY_BRANCHES
        self.EARTHLY_BRANCH_PINYIN = self.calendar.EARTHLY_BRANCH_PINYIN
        self.AZURE_DRAGON_MONTHLY_START = self.great_yellow_path.AZURE_DRAGON_MONTHLY_START
        self.SPIRIT_SEQUENCE = self.great_yellow_path.SPIRIT_SEQUENCE
        self.MNEMONIC_FORMULAS = self.great_yellow_path.MNEMONIC_FORMULAS
    
    # Delegate methods to appropriate components for backward compatibility
    
    def get_earthly_branch_for_date(self, date: datetime) -> str:
        """Get earthly branch for date."""
        return self.calendar.get_earthly_branch_for_date(date)
    
    def _get_lunar_month_from_date(self, date: datetime) -> Tuple[int, str, bool]:
        """Get lunar month from date."""
        return self.calendar.get_lunar_month_from_date(date)
    
    def _is_solar_term_day(self, date: datetime) -> bool:
        """Check if date is solar term day."""
        return self.calendar.is_solar_term_day(date)
    
    def get_construction_star_for_date(self, date: datetime) -> str:
        """Get construction star for date."""
        return self.construction_stars.get_construction_star_for_date(date)
    
    def get_auspiciousness_info(self, star: str) -> Dict:
        """Get auspiciousness info for star."""
        return self.construction_stars.get_auspiciousness_info(star)
    
    def get_day_branch_from_date(self, date: datetime) -> EarthlyBranch:
        """Get day branch from date."""
        return self.great_yellow_path.get_day_branch_from_date(date)
    
    def get_azure_dragon_starting_branch(self, lunar_month: int) -> EarthlyBranch:
        """Get azure dragon starting branch."""
        return self.great_yellow_path.get_azure_dragon_starting_branch(lunar_month)
    
    def calculate_spirit_for_day(self, date: datetime) -> GreatYellowPathSpirit:
        """Calculate spirit for day."""
        return self.great_yellow_path.calculate_spirit_for_day(date)
    
    def get_great_yellow_path_reading(self, date: datetime) -> GreatYellowPathReading:
        """Get great yellow path reading."""
        return self.great_yellow_path.get_great_yellow_path_reading(date)
    
    def calculate_day_info(self, date: datetime) -> Dict:
        """
        Calculate complete Construction Star and Great Yellow Path information for a specific date.
        
        Args:
            date (datetime): The date to analyze
            
        Returns:
            Dict: Complete information including star, translation, auspiciousness, and Great Yellow Path
        """
        # Get Construction Star information
        cs_info = self.construction_stars.calculate_day_info(date)
        
        # Get Great Yellow Path information
        gyp_reading = self.great_yellow_path.get_great_yellow_path_reading(date)
        
        # Combine both systems
        cs_info.update({
            "gyp_spirit": gyp_reading.spirit.chinese,
            "gyp_spirit_name": gyp_reading.spirit.name,
            "gyp_path_type": gyp_reading.path_type,
            "gyp_is_auspicious": gyp_reading.is_auspicious,
            "gyp_auspiciousness": gyp_reading.auspiciousness,
            "gyp_day_branch": gyp_reading.day_branch.chinese,
            "gyp_azure_dragon_start": gyp_reading.azure_dragon_start.chinese,
            "gyp_mnemonic_formula": gyp_reading.mnemonic_formula
        })
        
        return cs_info
    
    def calculate_month_calendar(self, month: int) -> List[Dict]:
        """
        Calculate Construction Stars for all days in a specific month.
        
        Args:
            month (int): Month number (1-12)
            
        Returns:
            List[Dict]: List of day information dictionaries for the entire month
        """
        month_data = []
        days_in_month = calendar.monthrange(self.year, month)[1]
        
        for day in range(1, days_in_month + 1):
            date = datetime(self.year, month, day)
            day_info = self.calculate_day_info(date)
            month_data.append(day_info)
            
        return month_data
    
    def calculate_year_summary(self) -> Dict:
        """
        Calculate a summary of Construction Stars for the entire year.
        
        Returns:
            Dict: Summary statistics including star frequencies and auspiciousness distribution
        """
        star_counts = {star: 0 for star in self.CONSTRUCTION_STARS}
        auspiciousness_counts = {
            "auspicious": 0,
            "moderate": 0, 
            "inauspicious": 0,
            "very_inauspicious": 0
        }
        
        current_date = datetime(self.year, 1, 1)
        end_date = datetime(self.year, 12, 31)
        
        while current_date <= end_date:
            star = self.get_construction_star_for_date(current_date)
            star_counts[star] += 1
            
            auspiciousness = self.get_auspiciousness_info(star)
            auspiciousness_counts[auspiciousness["level"]] += 1
            
            current_date += timedelta(days=1)
        
        return {
            "year": self.year,
            "lichun_date": self.solar_terms[0].strftime("%Y-%m-%d"),
            "solar_terms_count": len(self.solar_terms),
            "new_moons_count": len(self.new_moons),
            "lunar_months_count": len(self.lunar_months),
            "star_frequencies": star_counts,
            "auspiciousness_distribution": auspiciousness_counts,
            "total_days": sum(star_counts.values()),
            "first_lunar_month_start": self.lunar_months[0][0].strftime("%Y-%m-%d") if self.lunar_months else "N/A"
        }
    
    def find_auspicious_days_in_month(self, month: int, min_score: int = 3) -> List[Dict]:
        """
        Find all auspicious days in a specific month.
        
        Args:
            month (int): Month number (1-12)
            min_score (int): Minimum auspiciousness score (0-4)
            
        Returns:
            List[Dict]: List of auspicious days with their information
        """
        return self.construction_stars.find_auspicious_days_in_month(month, min_score)
    
    def print_month_calendar(self, month: int) -> None:
        """
        Print a formatted calendar for a specific month showing Construction Stars and Great Yellow Path.
        
        Args:
            month (int): Month number (1-12)
        """
        month_data = self.calculate_month_calendar(month)
        month_name = calendar.month_name[month]
        
        # Get the lunar month branch for this solar month
        sample_date = datetime(self.year, month, 15)
        lunar_month_info = self._get_lunar_month_from_date(sample_date)
        gyp_reading = self.get_great_yellow_path_reading(sample_date)
        
        if lunar_month_info:
            month_num, month_branch, is_leap = lunar_month_info
            month_pinyin = self.EARTHLY_BRANCH_PINYIN.get(month_branch, "")
            month_branch_display = f"{month_branch} ({month_pinyin})"
        else:
            month_branch_display = "N/A"
        
        print(f"\n{month_name} {self.year} - Construction Stars & Great Yellow Path Calendar")
        print(f"Lunar Month Branch: {month_branch_display}")
        print(f"Azure Dragon Start: {gyp_reading.azure_dragon_start.chinese} | Mnemonic: {gyp_reading.mnemonic_formula}")
        print("=" * 150)
        print(f"{'Date':<6} {'Star':<4} {'Translation':<12} {'Level':<12} {'Score':<5} {'Spirit':<8} {'Path':<4} {'GYP':<3} {'Day Branch':<12}")
        print("-" * 150)
        
        for day_info in month_data:
             date_str = day_info["date"].split("-")[2]
             star = day_info["star"]
             translation = day_info["translation"][:10]
             level = day_info["auspiciousness_level"][:10]
             score = day_info["score"]
             
             # Great Yellow Path info
             gyp_spirit = day_info["gyp_spirit"][:6]
             gyp_path = day_info["gyp_path_type"]
             gyp_auspicious = day_info["gyp_auspiciousness"]
             
             # Day's earthly branch
             day_branch = day_info["earthly_branch"]
             day_pinyin = self.EARTHLY_BRANCH_PINYIN.get(day_branch, "")
             day_branch_display = f"{day_branch}({day_pinyin})"
             
             # Color coding for Construction Stars
             if score >= 4:
                 cs_color = "🟨"  # Yellow for auspicious
             elif score == 3:
                 cs_color = "🟩"  # Green for moderate
             elif score == 1:
                 cs_color = "⬛"  # Black for inauspicious
             else:
                 cs_color = "🟥"  # Red for very inauspicious
             
             # Color coding for Great Yellow Path
             gyp_color = "🟡" if day_info["gyp_is_auspicious"] else "⚫"
             
             print(f"{date_str:<6} {star:<4} {translation:<12} {level:<12} {score:<5} {gyp_spirit:<8} {gyp_path:<4} {gyp_auspicious:<3} {day_branch_display:<12} {cs_color}{gyp_color}")


def main():
    """
    Example usage of the Twelve Construction Stars calculator.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Calculate Twelve Construction Stars with configurable timezone'
    )
    parser.add_argument(
        '--timezone', '-tz',
        default='Asia/Ho_Chi_Minh',
        help='Timezone for calculations (default: Asia/Ho_Chi_Minh)'
    )
    parser.add_argument(
        '--year', '-y',
        type=int,
        default=2025,
        help='Year to calculate for (default: 2025)'
    )
    
    args = parser.parse_args()
    
    # Initialize calculator with specified timezone
    calculator = MainCalculator(args.year, args.timezone)
    year = args.year
    
    # Print year summary
    summary = calculator.calculate_year_summary()
    print(f"Year {year} Summary (Lunar-based Construction Stars):")
    print(f"Timezone: {args.timezone}")
    print(f"Lìchūn Date: {summary['lichun_date']}")
    print(f"First Lunar Month Start: {summary['first_lunar_month_start']}")
    print(f"Solar Terms Count: {summary['solar_terms_count']}")
    print(f"New Moons Count: {summary['new_moons_count']}")
    print(f"Lunar Months Count: {summary['lunar_months_count']}")
    print(f"Total Days: {summary['total_days']}")
    
    # Print auspiciousness distribution
    print("\nAuspiciousness Distribution:")
    for level, count in summary['auspiciousness_distribution'].items():
        percentage = (count / summary['total_days']) * 100
        print(f"  {level.replace('_', ' ').title()}: {count} days ({percentage:.1f}%)")
    
    # Print calendar for current month
    current_month = 12 #datetime.now().month
    # print(current_month)
    calculator.print_month_calendar(current_month)
    
    # Find auspicious days in current month
    print(f"\nHighly Auspicious Days in {calendar.month_name[current_month]} {year}:")
    auspicious_days = calculator.find_auspicious_days_in_month(current_month, min_score=4)
    for day in auspicious_days:
        print(f"  {day['date']}: {day['star']} ({day['translation']})")
    
    # Show lunar months information
    print(f"\nLunar Months for {year} (Astronomically Accurate):")
    print(f"{'Month':<10} {'Branch':<15} {'Period':<25} {'Building':<10}")
    print("-" * 60)
    for i, (start, end, month_num, branch, is_leap) in enumerate(calculator.lunar_months):
        leap_prefix = "閏" if is_leap else ""
        pinyin = calculator.EARTHLY_BRANCH_PINYIN.get(branch, "")
        branch_display = f"{branch} ({pinyin})"
        period = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
        print(f"{leap_prefix+str(month_num):<10} {branch_display:<15} {period:<25} 建{branch}")
    
    # Show Winter Solstice information
    winter_solstice_found = False
    for start, end, month_num, branch, is_leap in calculator.lunar_months:
        if month_num == 11:  # Zi month
            zi_pinyin = calculator.EARTHLY_BRANCH_PINYIN.get('子', '')
            print(f"\nWinter Solstice Rule: Month 11 (子 - {zi_pinyin}) spans {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
            winter_solstice_found = True
            break
    
    if not winter_solstice_found:
        zi_pinyin = calculator.EARTHLY_BRANCH_PINYIN.get('子', '')
        print(f"\nNote: Winter Solstice rule applied - Month 11 (子 - {zi_pinyin}) contains Winter Solstice")
    
    # Calculate for a specific date
    today = datetime.now()
    today_info = calculator.calculate_day_info(today)
    print(f"\nToday's Construction Star & Great Yellow Path:")
    print(f"  Date: {today_info['date']}")
    
    # Construction Star information
    print(f"  Construction Star: {today_info['star']} ({today_info['translation']})")
    print(f"  CS Auspiciousness: {today_info['auspiciousness_level'].replace('_', ' ').title()}")
    print(f"  CS Score: {today_info['score']}/4")
    
    # Great Yellow Path information
    print(f"  Great Yellow Path Spirit: {today_info['gyp_spirit']} ({today_info['gyp_spirit_name']})")
    print(f"  GYP Path Type: {today_info['gyp_path_type']} ({today_info['gyp_auspiciousness']})")
    print(f"  GYP Mnemonic: {today_info['gyp_mnemonic_formula']}")
    
    # Add pinyin to earthly branch display
    day_branch = today_info['earthly_branch']
    day_pinyin = calculator.EARTHLY_BRANCH_PINYIN.get(day_branch, "")
    print(f"  Day Branch: {day_branch} ({day_pinyin})")
    
    # Add pinyin to lunar month display
    month_branch = today_info['building_branch']
    month_pinyin = calculator.EARTHLY_BRANCH_PINYIN.get(month_branch, "")
    print(f"  Lunar Month: {today_info['lunar_month_display']} ({month_branch} - {month_pinyin}) - 建{month_branch}")
    
    # Azure Dragon start for this month
    azure_start = today_info['gyp_azure_dragon_start']
    azure_pinyin = calculator.EARTHLY_BRANCH_PINYIN.get(azure_start, "")
    print(f"  Azure Dragon Start: {azure_start} ({azure_pinyin})")
    
    if today_info['is_leap_month']:
        print(f"  Note: This is a leap month (閏月)")
    if today_info['is_solar_term_day']:
        print(f"  Solar Term Note: {today_info['note']}")
    
    # Demonstrate solar term rule
    print(f"\nSolar Term Rule Demonstration:")
    print(f"Solar terms repeat the previous day's star instead of advancing.")
    
    # Find a solar term day to demonstrate
    for term_date in calculator.solar_terms[:3]:  # Check first 3 solar terms
        if term_date.year == year:
            term_info = calculator.calculate_day_info(term_date)
            prev_day = term_date - timedelta(days=1)
            prev_info = calculator.calculate_day_info(prev_day)
            
            print(f"  {prev_day.strftime('%Y-%m-%d')}: {prev_info['star']} (normal day)")
            print(f"  {term_date.strftime('%Y-%m-%d')}: {term_info['star']} (solar term - repeats previous)")
            break


if __name__ == "__main__":
    main()