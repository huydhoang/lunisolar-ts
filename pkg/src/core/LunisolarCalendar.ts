import type { TLunisolarDate } from '../types';
import { DataLoader } from '../data/DataLoader';
import { TimezoneHandler } from '../timezone/TimezoneHandler';

/**
 * Core LunisolarCalendar class.
 *
 * NOTE: This is a scaffold. The detailed calendar logic will be implemented next,
 * following docs/lunisolar_calendar_rules.md.
 */
export class LunisolarCalendar {
  // Readonly properties as per architecture
  readonly lunarYear!: number;
  readonly lunarMonth!: number;
  readonly lunarDay!: number;
  readonly isLeapMonth!: boolean;

  readonly yearStem!: string;
  readonly yearBranch!: string;
  readonly monthStem!: string;
  readonly monthBranch!: string;
  readonly dayStem!: string;
  readonly dayBranch!: string;
  readonly hourStem!: string;
  readonly hourBranch!: string;

  private constructor(init: TLunisolarDate) {
    Object.assign(this, init);
  }

  static async fromSolarDate(date: Date, timezone: string): Promise<LunisolarCalendar> {
    const tz = new TimezoneHandler(timezone);
    const parts = tz.utcToTimezoneDate(date);

    // Load surrounding years to cover boundaries across lunar year transitions
    const loader = new DataLoader({ baseUrl: './data' });
    const years = new Set([parts.year - 1, parts.year, parts.year + 1]);
    await Promise.all([
      ...Array.from(years).map((y) => loader.getNewMoons(y)),
      ...Array.from(years).map((y) => loader.getSolarTerms(y)),
    ]);

    // TODO: Implement:
    // - Determine correct lunar month from new moon data.
    // - Apply no-zhongqi rule for leap months.
    // - Compute lunar day number.
    // - Compute Gan-Zhi for year/month/day/hour with 23:00 boundary rule.

    // Temporary: throw to indicate not implemented yet to avoid misleading outputs.
    throw new Error('LunisolarCalendar.fromSolarDate: core calculation not implemented yet.');

    // Example shape once implemented:
    // return new LunisolarCalendar({
    //   lunarYear: 0,
    //   lunarMonth: 0,
    //   lunarDay: 0,
    //   isLeapMonth: false,
    //   yearStem: '', yearBranch: '',
    //   monthStem: '', monthBranch: '',
    //   dayStem: '', dayBranch: '',
    //   hourStem: '', hourBranch: '',
    // });
  }
}
