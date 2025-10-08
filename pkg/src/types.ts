/**
 * Core public types for the lunisolar-ts package.
 */

/** Unix timestamps in seconds for data arrays (smaller than ms). */
export type TSolarTerm = number;
export type TNewMoon = number;

/** Broken-out date parts in a specific timezone. */
export type TDateParts = {
  year: number;
  month: number; // 1-12
  day: number; // 1-31
  hour: number; // 0-23
  minute: number; // 0-59
  second: number; // 0-59
};

/** Canonical lunisolar date representation. */
export type TLunisolarDate = {
  lunarYear: number;
  lunarMonth: number; // 1-12
  lunarDay: number; // 1-30
  isLeapMonth: boolean;

  yearStem: string;
  yearBranch: string;
  monthStem: string;
  monthBranch: string;
  dayStem: string;
  dayBranch: string;
  hourStem: string;
  hourBranch: string;
};

/** 12 Construction Stars info */
export type TConstructionStar = {
  name: string;
  auspicious: boolean;
  score: number; // e.g., 0-100 normalized score
  description?: string;
};

export type TDayInfo = {
  date: Date;
  star: TConstructionStar;
};

/** Great Yellow Path spirit */
export type TGreatYellowPathSpirit = {
  name: string;
  type: 'Yellow Path' | 'Black Path';
  description?: string;
};
