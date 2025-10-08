// Example usage of the lunisolar-ts package after building.
// Run: npm run build && node ./examples/run.mjs

import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const dist = resolve(__dirname, '..', 'dist', 'index.mjs');

const { LunisolarCalendar, ConstructionStars, GreatYellowPath } = await import(pathToFileURL(dist).href);

async function show(date, timezone) {
  const cal = await LunisolarCalendar.fromSolarDate(date, timezone);
  const cs = new ConstructionStars(cal).getStar();
  const gyp = new GreatYellowPath(cal).getSpirit();

  console.log('--- Example ---');
  console.log('Solar:', date.toISOString(), 'TZ:', timezone);
  console.log('Lunisolar:', {
    year: cal.lunarYear,
    month: cal.lunarMonth,
    day: cal.lunarDay,
    isLeapMonth: cal.isLeapMonth,
    yearGanzhi: cal.yearStem + cal.yearBranch,
    monthGanzhi: cal.monthStem + cal.monthBranch,
    dayGanzhi: cal.dayStem + cal.dayBranch,
    hourGanzhi: cal.hourStem + cal.hourBranch,
  });
  console.log('isPrincipalSolarTermDay:', (cal).isPrincipalSolarTermDay);
  console.log('Construction Star:', cs.name, 'score=', cs.score);
  console.log('Great Yellow Path:', gyp.name, gyp.type);
  console.log();
}

// Asia/Ho_Chi_Minh example (UTC+7)
await show(new Date(Date.UTC(2025, 9, 8, 4, 0, 0)), 'Asia/Ho_Chi_Minh');

// Asia/Shanghai example (UTC+8)
await show(new Date(Date.UTC(2025, 5, 21, 4, 0, 0)), 'Asia/Shanghai');

// America/New_York example (UTC-4 or -5)
await show(new Date(Date.UTC(2025, 5, 21, 16, 0, 0)), 'America/New_York');
