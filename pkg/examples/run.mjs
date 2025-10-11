// Example usage of the lunisolar-ts package after building.
// Run: npm run build && node ./examples/run.mjs

import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const dist = resolve(__dirname, '..', 'dist', 'index.mjs');

const { configure, LunisolarCalendar, ConstructionStars, GreatYellowPath } = await import(
  pathToFileURL(dist).href
);

// Optional: Configure data loading strategy
// By default, the library uses a version-pinned CDN (zero-config)
// For local development, we can use the fs fallback:
configure({
  strategy: 'fetch',
  data: { baseUrl: './data' },
});

async function show(date, timezone) {
  const cal = await LunisolarCalendar.fromSolarDate(date, timezone);
  const cs = await new ConstructionStars(cal).getStar();
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
  console.log('isPrincipalSolarTermDay:', cal.isPrincipalSolarTermDay);
  console.log('Construction Star:', cs.name, 'score=', cs.score);
  console.log('Great Yellow Path:', gyp.name, gyp.type);
  console.log();
}

// Test case 1: 2025-10-08 12:00 Asia/Ho_Chi_Minh (UTC+7) - Should be lunar month 8
await show(new Date(Date.UTC(2025, 9, 8, 5, 0, 0)), 'Asia/Ho_Chi_Minh');

// Test case 2: 2025-08-23 12:00 Asia/Ho_Chi_Minh (UTC+7) - Should be lunar month 7
await show(new Date(Date.UTC(2025, 7, 23, 5, 0, 0)), 'Asia/Ho_Chi_Minh');

// Additional test: Asia/Shanghai example (UTC+8)
await show(new Date(Date.UTC(2025, 7, 23, 5, 0, 0)), 'Asia/Shanghai');

// Additional test: Construction Star sequence bug
for (let i = 0; i < 12; i++) {
  await show(new Date(Date.UTC(2025, 9, 8 + i, 5, 0, 0)), 'Asia/Ho_Chi_Minh');
}
