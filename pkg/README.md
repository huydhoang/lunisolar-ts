# lunisolar-ts (Phase 2 scaffold)

This is the initial scaffold for the TypeScript package of the Lunisolar Calendar system.

Scripts:
- `npm run build` — Build CJS and ESM outputs using Rollup
- `npm run typecheck` — Type-check the project
- `npm run lint` — Lint with ESLint
- `npm run format` — Format with Prettier

Next steps (Phase 3): implement DataLoader, TimezoneHandler, and LunisolarCalendar core as per docs.

API overview
- Core
  - LunisolarCalendar.fromSolarDate(date: Date, timezone: string): Promise<LunisolarCalendar>
  - calendar getters: lunarYear, lunarMonth, lunarDay, isLeapMonth, yearStem/Branch, monthStem/Branch, dayStem/Branch, hourStem/Branch, isPrincipalSolarTermDay
- Huangdao
  - ConstructionStars
    - constructor(calendar: LunisolarCalendar)
    - getStar(): TConstructionStar
    - getStar(): TConstructionStar respects principal solar term day repetition via calendar.isPrincipalSolarTermDay
    - getStarWithSolarTermRule(...): deprecated
    - static getAuspiciousDays(year: number, month: number, minScore: number): Promise<TDayInfo[]>
  - GreatYellowPath
    - constructor(calendar: LunisolarCalendar)
    - getSpirit(): TGreatYellowPathSpirit

Usage examples
```ts
import { LunisolarCalendar, ConstructionStars, GreatYellowPath } from 'lunisolar-ts';

const now = new Date();
const cal = await LunisolarCalendar.fromSolarDate(now, 'Asia/Ho_Chi_Minh');

const cs = new ConstructionStars(cal);
const star = await cs.getStarWithSolarTermRule(now, 'Asia/Ho_Chi_Minh');

const gyp = new GreatYellowPath(cal).getSpirit();
console.log(star.name, gyp.name);
```
