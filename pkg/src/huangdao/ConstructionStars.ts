import type { TConstructionStar, TDayInfo } from '../types';
import { LunisolarCalendar } from '../core/LunisolarCalendar';

// Twelve Construction Stars in fixed order
const STAR_SEQUENCE = ['建', '除', '满', '平', '定', '执', '破', '危', '成', '收', '开', '闭'] as const;

// Month 1..12 -> Building Branch (月建) mapping
// 1: 寅, 2: 卯, 3: 辰, 4: 巳, 5: 午, 6: 未, 7: 申, 8: 酉, 9: 戌, 10: 亥, 11: 子, 12: 丑
const MONTH_BUILDING_BRANCH: Record<number, string> = {
  1: '寅', 2: '卯', 3: '辰', 4: '巳', 5: '午', 6: '未', 7: '申', 8: '酉', 9: '戌', 10: '亥', 11: '子', 12: '丑',
};

// Scoring and auspiciousness per traditional formula
// 建满平收黑，除危定执黄，成开皆可用，破闭不可当
const STAR_SCORES: Record<string, { auspicious: boolean; score: number; description: string }> = {
  '建': { auspicious: false, score: 1, description: 'Establish; inauspicious for major starts' },
  '除': { auspicious: true, score: 4, description: 'Remove; highly auspicious' },
  '满': { auspicious: false, score: 1, description: 'Full; avoid new starts' },
  '平': { auspicious: false, score: 1, description: 'Balanced; generally inauspicious' },
  '定': { auspicious: true, score: 4, description: 'Set; highly auspicious' },
  '执': { auspicious: true, score: 4, description: 'Hold; highly auspicious' },
  '破': { auspicious: false, score: 0, description: 'Break; very inauspicious' },
  '危': { auspicious: true, score: 4, description: 'Danger; paradoxically auspicious' },
  '成': { auspicious: true, score: 3, description: 'Accomplish; moderately good' },
  '收': { auspicious: false, score: 1, description: 'Harvest; inauspicious for new ventures' },
  '开': { auspicious: true, score: 3, description: 'Open; moderately good' },
  '闭': { auspicious: false, score: 0, description: 'Close; very inauspicious' },
};

// Earthly branch index helper (子=0 .. 亥=11)
const BRANCH_INDEX: Record<string, number> = {
  '子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5, '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11,
};

/**
 * Twelve Construction Stars (十二建星) calculator.
 *
 * Usage: construct with an existing LunisolarCalendar instance, then call getStar().
 * For the solar-term-day repetition rule, use getStarWithSolarTermRule(date, timezone).
 */
export class ConstructionStars {
  private calendar: LunisolarCalendar;

  constructor(calendar: LunisolarCalendar) {
    this.calendar = calendar;
  }

  /**
   * Compute Construction Star for the calendar’s current date using branch difference:
   * starIndex = (dayBranchIndex - buildingBranchIndex) mod 12.
   */
  getStar(): TConstructionStar {
    const lunarMonth = this.calendar.lunarMonth;
    const dayBranch = this.calendar.dayBranch; // e.g., '子','丑',...
    const buildingBranch = MONTH_BUILDING_BRANCH[lunarMonth];

    let dIdx = BRANCH_INDEX[dayBranch];
    const mIdx = BRANCH_INDEX[buildingBranch];

    // If today is a principal solar term day in the calendar's timezone, repeat previous day's star
    if ((this.calendar as any).isPrincipalSolarTermDay) {
      dIdx = (dIdx + 12 - 1) % 12; // shift to previous day's branch
    }

    const starIdx = ((dIdx - mIdx) % 12 + 12) % 12;
    const name = STAR_SEQUENCE[starIdx];
    const meta = STAR_SCORES[name];

    return {
      name,
      auspicious: meta.auspicious,
      score: meta.score,
      description: meta.description,
    };
  }

  /**
   * @deprecated This method is deprecated. ConstructionStars.getStar() now respects
   * principal solar term day repetition via calendar.isPrincipalSolarTermDay.
   */
  async getStarWithSolarTermRule(_date: Date, _timezone: string): Promise<TConstructionStar> {
    // Behavior now handled in getStar()
    return this.getStar();
  }

  // Convenience: list days in a solar month that meet a minimum score
  // Note: uses local timezone of the provided calendar’s day as reference for constructing Date instances
  static async getAuspiciousDays(year: number, month: number, minScore: number): Promise<TDayInfo[]> {
    const results: TDayInfo[] = [];
    const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate(); // month is 1-based

    for (let day = 1; day <= daysInMonth; day++) {
      // Noon UTC chosen to avoid boundary issues; consumers should pass correct timezone when creating calendar
      const dt = new Date(Date.UTC(year, month - 1, day, 4, 0, 0));
      let cal: LunisolarCalendar;
      try {
        cal = await LunisolarCalendar.fromSolarDate(dt, 'Asia/Shanghai');
      } catch {
        continue;
      }
      const cs = new ConstructionStars(cal).getStar();
      if (cs.score >= minScore) {
        results.push({ date: cal.getSolarDate(), star: cs });
      }
    }

    return results;
  }
}
