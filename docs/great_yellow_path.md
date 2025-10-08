# Great Yellow Path (大黄道) System - Detailed Documentation

## Table of Contents
1. [Overview](#overview)
2. [Historical Background](#historical-background)
3. [Core Principles](#core-principles)
4. [System Architecture](#system-architecture)
5. [Implementation Details](#implementation-details)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)
8. [Testing and Validation](#testing-and-validation)
9. [Cultural Significance](#cultural-significance)
10. [Troubleshooting](#troubleshooting)

## Overview

The Great Yellow Path (大黄道) system is a sophisticated Chinese auspicious day calculation method that determines favorable and unfavorable dates based on the cyclical interaction of twelve spirits with earthly branches. This implementation provides a faithful reproduction of traditional formulas while incorporating modern computational accuracy.

### Key Features
- **Monthly Rotation**: Azure Dragon starting position rotates monthly according to traditional mnemonic formulas
- **Solar Terms Integration**: Uses authentic lunar months defined by the 24 solar terms
- **Comprehensive Spirit System**: All twelve spirits with detailed cultural descriptions
- **Accurate Day Branch Calculation**: Corrected reference point for precise earthly branch determination
- **Validation Framework**: Built-in validation of traditional mnemonic formulas

### Quick Start
```python
from datetime import datetime
from calculate_great_yellow_path import GreatYellowPathCalculator

# Initialize calculator
calc = GreatYellowPathCalculator()

# Get reading for a specific date
date = datetime(2025, 7, 1)
reading = calc.get_day_reading(date)
print(f"{reading.spirit.chinese} - {reading.path_type}")
# Output: 玄武 - Black Path
```

## Historical Background

The Great Yellow Path system represents one of the most sophisticated approaches to Chinese auspicious day selection, with roots extending back over a millennium. Unlike simpler fixed-starting systems, this method incorporates:

- **Ancient Astronomical Observations**: Based on careful observation of celestial cycles
- **Cyclical Time Philosophy**: Reflects the Chinese understanding of time as cyclical rather than linear
- **Regional Variations**: Adapted across different regions of Asia with local modifications
- **Practical Wisdom**: Accumulated knowledge for timing important life events

### Traditional Sources
The system draws from classical texts including:
- **Yùxiá Jì (《玉匣记》)**: "Jade Box Records" - comprehensive divination manual
- **Tōngshū (通书)**: Traditional Chinese almanacs
- **Regional Folk Traditions**: Oral transmission of calculation methods

## Core Principles

### The Twelve Spirits (十二神)

The system revolves around twelve spirits that govern different aspects of daily activities:

#### Yellow Path Days (黄道日) - Auspicious
1. **青龙 (Qinglong) - Azure Dragon**
   - Traditional: 天乙星，天贵星，利有攸往，所作必成，所求皆得
   - Modern: Auspicious for all activities, especially important endeavors and travel

2. **明堂 (Mingtang) - Bright Hall**
   - Traditional: 贵人星，明辅星，利见大人，利有攸往，作事必成
   - Modern: Favorable for meetings with important people, ceremonies, and official business

3. **金匮 (Jinkui) - Golden Coffer**
   - Traditional: 福德星，利释道用事，阍者女子用事，吉。宜嫁娶，不宜整戎伍
   - Modern: Good for financial matters, religious activities, and weddings

4. **天德 (Tiande) - Heavenly Virtue**
   - Traditional: 宝光星，天德星，其时大郭，作事有成，利有攸往，出行吉
   - Modern: Excellent for travel, important decisions, and virtuous activities

5. **玉堂 (Yutang) - Jade Hall**
   - Traditional: 天开星，百事吉，求事成，出行有财，宜文书喜庆之事，利见大人，利安葬，不利泥灶
   - Modern: Favorable for documents, celebrations, meetings with dignitaries, and burials

6. **司命 (Siming) - Life Controller**
   - Traditional: 凤辇星，此时从寅至申时用事大吉，从酉至丑时有事不吉，即白天吉，晚上不利
   - Modern: Good for health and longevity matters, but only during daytime hours (寅-申)

#### Black Path Days (黑道日) - Inauspicious
1. **天刑 (Tianxing) - Heavenly Punishment**
   - Traditional: 天刑星，利于出师，战无不克，其它动作谋为皆不宜用，大忌词讼
   - Modern: Avoid legal matters and conflicts; only suitable for military activities

2. **朱雀 (Zhuque) - Vermillion Bird**
   - Traditional: 天讼星，利用公事，常人凶，诸事忌用，谨防争讼
   - Modern: Unfavorable for communication and personal matters; beware of disputes

3. **白虎 (Baihu) - White Tiger**
   - Traditional: 天杀星，宜出师畋猎祭祀，皆吉，其余都不利
   - Modern: Dangerous day; only suitable for military expeditions, hunting, and sacrifices

4. **天牢 (Tianlao) - Heavenly Prison**
   - Traditional: 镇神星，阴人用事皆吉，其余都不利
   - Modern: Restrictive day; only favorable for women's activities

5. **玄武 (Xuanwu) - Black Tortoise**
   - Traditional: 天狱星，君子用之吉，小人用之凶，忌词讼博戏
   - Modern: Day of hidden dangers; avoid legal matters and gambling

6. **勾陈 (Gouchen) - Coiling Snake**
   - Traditional: 地狱星，起造安葬，犯此绝嗣。此时所作一切事，有始无终，先喜后悲，不利攸往
   - Modern: Day of entanglements and delays; avoid construction and burials

### Traditional Mnemonic Formula (口诀)

The Azure Dragon starting position for each month follows the traditional mnemonic:

```
寅申需加子，卯酉却在寅
辰戍龙位上，巳亥午上存
子午临申地，丑未戍上行
```

This translates to:
- **Months 1&7 (寅申)**: Azure Dragon starts at 子 (Zi)
- **Months 2&8 (卯酉)**: Azure Dragon starts at 寅 (Yin)
- **Months 3&9 (辰戍)**: Azure Dragon starts at 辰 (Chen)
- **Months 4&10 (巳亥)**: Azure Dragon starts at 午 (Wu)
- **Months 5&11 (子午)**: Azure Dragon starts at 申 (Shen)
- **Months 6&12 (丑未)**: Azure Dragon starts at 戌 (Xu)

### Earthly Branches (十二地支)

The system uses the twelve earthly branches, each associated with a zodiac animal:

| Index | Chinese | Animal | Time Period |
|-------|---------|--------|--------------|
| 0 | 子 (Zi) | Rat | 23:00-01:00 |
| 1 | 丑 (Chou) | Ox | 01:00-03:00 |
| 2 | 寅 (Yin) | Tiger | 03:00-05:00 |
| 3 | 卯 (Mao) | Rabbit | 05:00-07:00 |
| 4 | 辰 (Chen) | Dragon | 07:00-09:00 |
| 5 | 巳 (Si) | Snake | 09:00-11:00 |
| 6 | 午 (Wu) | Horse | 11:00-13:00 |
| 7 | 未 (Wei) | Goat | 13:00-15:00 |
| 8 | 申 (Shen) | Monkey | 15:00-17:00 |
| 9 | 酉 (You) | Rooster | 17:00-19:00 |
| 10 | 戌 (Xu) | Dog | 19:00-21:00 |
| 11 | 亥 (Hai) | Pig | 21:00-23:00 |

## System Architecture

### Class Structure

```python
class GreatYellowPathCalculator:
    """Main calculator class for the Great Yellow Path system."""
    
    # Core data structures
    AZURE_DRAGON_MONTHLY_START: Dict[int, EarthlyBranch]
    MONTH_CONSTRUCTION: Dict[int, EarthlyBranch]
    SPIRIT_SEQUENCE: List[GreatYellowPathSpirit]
    MNEMONIC_FORMULAS: Dict[int, str]
```

### Data Models

```python
@dataclass
class GreatYellowPathReading:
    """Complete reading for a specific day."""
    date: datetime
    lunar_month: int
    day_branch: EarthlyBranch
    spirit: GreatYellowPathSpirit
    path_type: str
    is_auspicious: bool
    azure_dragon_start: EarthlyBranch
    mnemonic_validation: str
```

### Calculation Flow

1. **Date Input** → Gregorian calendar date
2. **Lunar Month Determination** → Based on solar terms or lunar calendar boundaries
3. **Azure Dragon Start** → Retrieved from monthly mapping using mnemonic formula
4. **Day Branch Calculation** → Earthly branch for the specific date
5. **Spirit Calculation** → Offset from Azure Dragon start applied to spirit sequence
6. **Reading Generation** → Complete auspiciousness assessment

## Implementation Details

### Day Branch Calculation

The system uses a corrected reference point for accurate day branch calculation:

```python
def get_day_branch_from_date(self, date: datetime) -> EarthlyBranch:
    # Reference: January 1, 2000 was a 戊午 (Wu) day
    reference_date = datetime(2000, 1, 1)
    reference_branch_index = 6  # Wu = 6
    
    days_elapsed = (date - reference_date).days
    branch_index = (reference_branch_index + days_elapsed) % 12
    
    return EarthlyBranch(branch_index)
```

### Lunar Month Determination

For 2025, the system uses accurate lunar calendar boundaries that account for the leap month:

```python
lunar_month_boundaries_2025 = {
    1: (datetime(2025, 1, 29), datetime(2025, 2, 27)),
    2: (datetime(2025, 2, 28), datetime(2025, 3, 28)),
    # ... more months
    6: (datetime(2025, 6, 25), datetime(2025, 8, 22)),  # Includes leap month
    # ... remaining months
}
```

For other years, it falls back to solar terms calculation.

### Spirit Calculation Algorithm

```python
def calculate_spirit_for_day(self, date: datetime) -> GreatYellowPathSpirit:
    lunar_month = self.get_lunar_month_from_date(date)
    azure_dragon_start = self.get_azure_dragon_starting_branch(lunar_month)
    day_branch = self.get_day_branch_from_date(date)
    
    # Calculate offset and apply to spirit sequence
    offset = (day_branch.index - azure_dragon_start.index) % 12
    spirit_index = offset % 12
    
    return self.SPIRIT_SEQUENCE[spirit_index]
```

### Validation Framework

The system includes comprehensive validation:

```python
def _validate_system_integrity(self) -> None:
    """Validate system configuration on initialization."""
    if len(self.SPIRIT_SEQUENCE) != 12:
        raise ValueError("Spirit sequence must contain exactly 12 spirits")
    
    auspicious_count = sum(1 for spirit in self.SPIRIT_SEQUENCE if spirit.is_auspicious)
    if auspicious_count != 6:
        raise ValueError("Must have exactly 6 auspicious and 6 inauspicious spirits")
```

## API Reference

### Core Methods

#### `get_day_reading(date: datetime) -> GreatYellowPathReading`
Returns complete auspiciousness information for a specific date.

**Parameters:**
- `date`: The date to analyze

**Returns:**
- `GreatYellowPathReading`: Complete reading with spirit, path type, and cultural information

**Example:**
```python
reading = calc.get_day_reading(datetime(2025, 7, 1))
print(f"Spirit: {reading.spirit.chinese}")
print(f"Auspicious: {reading.is_auspicious}")
```

#### `get_month_calendar(year: int, lunar_month: int) -> List[GreatYellowPathReading]`
Generates a complete calendar for a lunar month.

**Parameters:**
- `year`: The year (integer)
- `lunar_month`: Lunar month number (1-12)

**Returns:**
- `List[GreatYellowPathReading]`: Readings for all days in the month

#### `get_yellow_path_days_in_month(year: int, lunar_month: int) -> List[GreatYellowPathReading]`
Returns only auspicious days in a lunar month.

#### `get_black_path_days_in_month(year: int, lunar_month: int) -> List[GreatYellowPathReading]`
Returns only inauspicious days in a lunar month.

### Utility Methods

#### `get_azure_dragon_starting_branch(lunar_month: int) -> EarthlyBranch`
Returns the Azure Dragon starting branch for a given lunar month.

#### `validate_mnemonic_formula() -> Dict[int, bool]`
Validates the implementation against traditional mnemonic formulas.

#### `print_month_calendar(year: int, lunar_month: int) -> None`
Prints a formatted calendar with detailed information for each day.

## Usage Examples

### Basic Day Reading

```python
from datetime import datetime
from calculate_great_yellow_path import GreatYellowPathCalculator

calc = GreatYellowPathCalculator()
date = datetime(2025, 7, 1)
reading = calc.get_day_reading(date)

print(f"Date: {date.strftime('%Y-%m-%d')}")
print(f"Lunar Month: {reading.lunar_month}")
print(f"Day Branch: {reading.day_branch.chinese} ({reading.day_branch.animal})")
print(f"Spirit: {reading.spirit.chinese} ({reading.spirit.english})")
print(f"Path Type: {reading.path_type}")
print(f"Traditional Description: {reading.spirit.traditional_description}")
```

### Monthly Calendar Generation

```python
# Generate calendar for lunar month 6 of 2025
calendar = calc.get_month_calendar(2025, 6)

print(f"Total days: {len(calendar)}")
for reading in calendar[:5]:  # Show first 5 days
    status = "🟡" if reading.is_auspicious else "⚫"
    print(f"{status} {reading.date.strftime('%m-%d')} | {reading.spirit.chinese}")
```

### Finding Auspicious Days

```python
# Find all auspicious days in a month
yellow_days = calc.get_yellow_path_days_in_month(2025, 6)

print(f"Auspicious days in lunar month 6:")
for reading in yellow_days:
    print(f"🟡 {reading.date.strftime('%Y-%m-%d')} | {reading.spirit.chinese}")
    print(f"   Good for: {reading.spirit.modern_description}")
```

### Batch Processing

```python
# Analyze multiple dates
dates = [
    datetime(2025, 6, 15),
    datetime(2025, 7, 1),
    datetime(2025, 8, 15)
]

for date in dates:
    reading = calc.get_day_reading(date)
    print(f"{date.strftime('%Y-%m-%d')}: {reading.spirit.chinese} ({reading.path_type})")
```

### Validation and Debugging

```python
# Validate mnemonic formula implementation
validation = calc.validate_mnemonic_formula()
for month, is_valid in validation.items():
    status = "✓" if is_valid else "✗"
    formula = calc.MNEMONIC_FORMULAS[month]
    print(f"{status} Month {month}: {formula}")
```

## Testing and Validation

### Built-in Test Suite

The system includes a comprehensive test function:

```python
def test_great_yellow_path_2025_month_6():
    """Test the Great Yellow Path system for 2025 lunar month 6."""
    # Validates mnemonic formulas
    # Tests specific month calculations
    # Generates complete calendar
    # Provides summary statistics
```

Run the test:
```bash
python calculate_great_yellow_path.py
```

### Validation Checkpoints

1. **Mnemonic Formula Accuracy**: Ensures Azure Dragon starting positions match traditional formulas
2. **Spirit Sequence Integrity**: Validates 6 auspicious and 6 inauspicious spirits
3. **Day Branch Calculation**: Verified against known reference dates
4. **Lunar Month Boundaries**: Accurate for 2025 including leap month handling

### Known Test Cases

- **July 1, 2025**: Should be Lunar Month 6, Day 7, 未 day, 玄武 spirit (Black Path)
- **Mnemonic Formula**: All 12 months should validate correctly
- **Spirit Distribution**: Exactly 50% auspicious days over time

## Cultural Significance

### Traditional Applications

- **Wedding Planning**: Selecting auspicious dates for ceremonies
- **Business Ventures**: Timing important business decisions
- **Travel**: Choosing favorable departure dates
- **Construction**: Starting building projects on auspicious days
- **Medical Procedures**: Traditional timing for health-related activities

### Regional Variations

While the core system remains consistent, regional adaptations exist:
- **Chinese Mainland**: Standard implementation as documented
- **Taiwan**: Minor variations in solar terms calculation
- **Southeast Asia**: Local cultural adaptations of spirit interpretations
- **Overseas Chinese Communities**: Simplified versions for practical use

### Modern Relevance

The system continues to be relevant in contemporary contexts:
- **Cultural Preservation**: Maintaining traditional knowledge
- **Personal Planning**: Individual decision-making framework
- **Academic Research**: Study of traditional Chinese cosmology
- **Software Applications**: Integration into calendar and planning apps

## Troubleshooting

### Common Issues

#### Incorrect Day Branch Calculation
**Problem**: Day branch doesn't match expected values
**Solution**: Verify reference date (January 1, 2000 = Wu day)

```python
# Debug day branch calculation
test_date = datetime(2000, 1, 1)
branch = calc.get_day_branch_from_date(test_date)
print(f"Jan 1, 2000 should be Wu (午): {branch.chinese}")  # Should print 午
```

#### Lunar Month Boundary Issues
**Problem**: Date falls in wrong lunar month
**Solution**: Check lunar calendar boundaries for the specific year

```python
# Debug lunar month determination
date = datetime(2025, 7, 1)
lunar_month = calc.get_lunar_month_from_date(date)
print(f"July 1, 2025 lunar month: {lunar_month}")  # Should be 6
```

#### Mnemonic Formula Validation Failures
**Problem**: Traditional formulas don't validate
**Solution**: Check Azure Dragon starting positions

```python
# Debug mnemonic validation
validation = calc.validate_mnemonic_formula()
for month, valid in validation.items():
    if not valid:
        print(f"Month {month} validation failed")
        print(f"Expected: {calc.MNEMONIC_FORMULAS[month]}")
        print(f"Actual start: {calc.AZURE_DRAGON_MONTHLY_START[month].chinese}")
```

### Performance Considerations

- **Solar Terms Calculation**: Cached per year for efficiency
- **Batch Processing**: Use `get_month_calendar()` for multiple dates in same month
- **Memory Usage**: Minimal - all calculations are stateless

### Error Handling

The system includes comprehensive error handling:

```python
try:
    reading = calc.get_day_reading(invalid_date)
except ValueError as e:
    print(f"Invalid date: {e}")

try:
    calendar = calc.get_month_calendar(2025, 13)  # Invalid month
except ValueError as e:
    print(f"Invalid month: {e}")
```

### Debugging Tools

```python
# Enable detailed debugging
def debug_calculation(date):
    lunar_month = calc.get_lunar_month_from_date(date)
    azure_start = calc.get_azure_dragon_starting_branch(lunar_month)
    day_branch = calc.get_day_branch_from_date(date)
    
    print(f"Date: {date}")
    print(f"Lunar Month: {lunar_month}")
    print(f"Azure Dragon Start: {azure_start.chinese}")
    print(f"Day Branch: {day_branch.chinese}")
    print(f"Offset: {(day_branch.index - azure_start.index) % 12}")
    
    spirit = calc.calculate_spirit_for_day(date)
    print(f"Spirit: {spirit.chinese}")
```

---

## Conclusion

The Great Yellow Path system represents a sophisticated integration of astronomical observation, mathematical calculation, and cultural wisdom. This implementation provides both historical accuracy and modern computational efficiency, making ancient wisdom accessible for contemporary use while maintaining respect for traditional foundations.

For additional support or questions about the implementation, refer to the source code comments and test functions, which provide extensive examples and validation procedures.