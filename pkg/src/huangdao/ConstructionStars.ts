import type { TConstructionStar, TDayInfo } from '../types';
import { LunisolarCalendar } from '../core/LunisolarCalendar';

// Twelve Construction Stars in fixed order
const STAR_SEQUENCE = [
  '建',
  '除',
  '满',
  '平',
  '定',
  '执',
  '破',
  '危',
  '成',
  '收',
  '开',
  '闭',
] as const;

// Reverse mapping (index -> branch char)
const BRANCH_ORDER = [
  '子',
  '丑',
  '寅',
  '卯',
  '辰',
  '巳',
  '午',
  '未',
  '申',
  '酉',
  '戌',
  '亥',
] as const;

// Month 1..12 -> Building Branch (月建) mapping
// 1: 寅, 2: 卯, 3: 辰, 4: 巳, 5: 午, 6: 未, 7: 申, 8: 酉, 9: 戌, 10: 亥, 11: 子, 12: 丑
const MONTH_BUILDING_BRANCH: Record<number, string> = {
  1: '寅',
  2: '卯',
  3: '辰',
  4: '巳',
  5: '午',
  6: '未',
  7: '申',
  8: '酉',
  9: '戌',
  10: '亥',
  11: '子',
  12: '丑',
};

// Scoring and auspiciousness per traditional formula
// 建满平收黑，除危定执黄，成开皆可用，破闭不可当
// Updated scoring: 4 (auspicious), 3 (moderate), 2 (inauspicious), 1 (very inauspicious)
const STAR_SCORES: Record<string, { auspicious: boolean; score: number; description: string }> = {
  建: { auspicious: false, score: 2, description: 'Establish; inauspicious for major starts' },
  除: { auspicious: true, score: 4, description: 'Remove; highly auspicious' },
  满: { auspicious: false, score: 2, description: 'Full; avoid new starts' },
  平: { auspicious: false, score: 2, description: 'Balanced; generally inauspicious' },
  定: { auspicious: true, score: 4, description: 'Set; highly auspicious' },
  执: { auspicious: true, score: 4, description: 'Hold; highly auspicious' },
  破: { auspicious: false, score: 1, description: 'Break; very inauspicious' },
  危: { auspicious: true, score: 4, description: 'Danger; paradoxically auspicious' },
  成: { auspicious: true, score: 3, description: 'Accomplish; moderately good' },
  收: { auspicious: false, score: 2, description: 'Harvest; inauspicious for new ventures' },
  开: { auspicious: true, score: 3, description: 'Open; moderately good' },
  闭: { auspicious: false, score: 1, description: 'Close; very inauspicious' },
};

// Earthly branch index helper (子=0 .. 亥=11)
const BRANCH_INDEX: Record<string, number> = {
  子: 0,
  丑: 1,
  寅: 2,
  卯: 3,
  辰: 4,
  巳: 5,
  午: 6,
  未: 7,
  申: 8,
  酉: 9,
  戌: 10,
  亥: 11,
};

/**
 * Twelve Construction Stars (十二建星) calculator.
 *
 * Usage: construct with an existing LunisolarCalendar instance, then call getStar().
 * For the solar-term-day repetition rule, use getStarWithSolarTermRule(date, timezone).
 */
export class ConstructionStars {
  private calendar: LunisolarCalendar;
  // private debug: boolean = true; // Enable detailed debug logs by default

  constructor(calendar: LunisolarCalendar) {
    this.calendar = calendar;
  }

  /**
   * Accurate star calculation that auto-applies solar-term repeat rule for single-day queries.
   * It inspects the previous solar day in the same timezone to decide whether to use the
   * previous-day base star (on solar-term day and the day after).
   */
  async getStar(): Promise<TConstructionStar> {
    const lunarMonth = this.calendar.lunarMonth;
    const dayBranch = this.calendar.dayBranch;
    const buildingBranch = MONTH_BUILDING_BRANCH[lunarMonth];
    const isSolarTermToday = (this.calendar as any).isPrincipalSolarTermDay;
    const tz = (this.calendar as any).timezone ?? 'Asia/Shanghai';

    const dIdx = BRANCH_INDEX[dayBranch];
    const mIdx = BRANCH_INDEX[buildingBranch];
    const baseStarIdx = (((dIdx - mIdx) % 12) + 12) % 12;
    const baseStar = STAR_SEQUENCE[baseStarIdx];

    // Previous day calendar in the SAME timezone
    const solarDate = this.calendar.getSolarDate();
    const prevDate = new Date(solarDate.getTime() - 24 * 60 * 60 * 1000);
    let prevCal: LunisolarCalendar | null = null;
    try {
      prevCal = await LunisolarCalendar.fromSolarDate(prevDate, tz);
    } catch {
      prevCal = null;
    }

    const prevWasSolarTerm = prevCal ? (prevCal as any).isPrincipalSolarTermDay : false;
    const prevMonth = prevCal ? prevCal.lunarMonth : lunarMonth;
    const prevDayBranch = prevCal ? prevCal.dayBranch : BRANCH_ORDER[(dIdx + 11) % 12];
    const prevBuildingBranch = MONTH_BUILDING_BRANCH[prevMonth];
    const prevDIdx = BRANCH_INDEX[prevDayBranch];
    const prevMIdx = BRANCH_INDEX[prevBuildingBranch];
    const prevBaseStarIdx = (((prevDIdx - prevMIdx) % 12) + 12) % 12;
    const prevBaseStar = STAR_SEQUENCE[prevBaseStarIdx];

    let actualStar: string;
    if (isSolarTermToday || prevWasSolarTerm) {
      // On solar-term day and the day after, actual star equals previous day's BASE star
      actualStar = prevBaseStar;
    } else {
      actualStar = baseStar;
    }

    // if (this.debug) {
    //   console.log('[ConstructionStars] Accurate calc details:', {
    //     solarDateISO: solarDate.toISOString(),
    //     timezone: tz,
    //     today: {
    //       lunarMonth,
    //       dayBranch,
    //       buildingBranch,
    //       indices: { dIdx, mIdx },
    //       baseStarIdx,
    //       baseStar,
    //       isSolarTermToday,
    //     },
    //     prev: {
    //       dateISO: prevDate.toISOString(),
    //       lunarMonth: prevMonth,
    //       dayBranch: prevDayBranch,
    //       buildingBranch: prevBuildingBranch,
    //       indices: { prevDIdx, prevMIdx },
    //       baseStarIdx: prevBaseStarIdx,
    //       baseStar: prevBaseStar,
    //       prevWasSolarTerm,
    //     },
    //     actualStar,
    //   });
    // }

    const meta = STAR_SCORES[actualStar];
    return {
      name: actualStar,
      auspicious: meta.auspicious,
      score: meta.score,
      description: meta.description,
    };
  }

  // Convenience: list days in a solar month that meet a minimum score
  // Note: uses local timezone of the provided calendar's day as reference for constructing Date instances
  static async getAuspiciousDays(
    year: number,
    month: number,
    minScore: number,
    timezone: string = 'Asia/Shanghai',
  ): Promise<TDayInfo[]> {
    const results: TDayInfo[] = [];
    const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate(); // month is 1-based

    let prevStar: string | null = null;
    let prevWasSolarTerm = false;

    for (let day = 1; day <= daysInMonth; day++) {
      // Noon UTC chosen to avoid boundary issues
      const dt = new Date(Date.UTC(year, month - 1, day, 4, 0, 0));
      let cal: LunisolarCalendar;
      try {
        cal = await LunisolarCalendar.fromSolarDate(dt, timezone);
      } catch {
        continue;
      }

      // Create ConstructionStars with sequential tracking
      const cs = new ConstructionStars(cal);
      const star = await cs.getStar();

      // Update tracking for next iteration
      prevStar = star.name;
      prevWasSolarTerm = (cal as any).isPrincipalSolarTermDay;

      if (star.score >= minScore) {
        results.push({ date: cal.getSolarDate(), star });
      }
    }

    return results;
  }
}
