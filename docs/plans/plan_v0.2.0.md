# Plan v0.2.0: Serverless Data Loading Implementation (Revised)

This document outlines the development tasks required to implement the serverless-friendly data loading strategies. This revised plan clarifies the implementation details and adjusts the build process to ensure both dynamic fetching and static bundling are correctly supported.

## 1. Configuration and Core Module Refactoring

-   [ ] **Create a Global Configuration Module (`src/config.ts`)**.
    -   This module will hold the user-defined configuration, such as `{ strategy: 'fetch', baseUrl: '...' }`.
    -   It will export a getter for the config and a setter function.

-   [ ] **Implement a Top-Level `configure` Function (`src/index.ts`)**.
    -   Export a new function `configure(options: LunisolarOptions)` that allows users to set the data loading strategy.
    -   This function will call the setter in `src/config.ts`.

-   [ ] **Refactor the Existing `DataLoader` (`src/data/DataLoader.ts`)**.
    -   Remove the constructor options. The `DataLoader` should be a singleton-like class that reads from the global config module (`src/config.ts`).
    -   Modify the `_loadJson` method to implement the new loading strategies based on the global configuration.

-   [ ] **Update Type Definitions (`src/types.ts`)**.
    -   Add `LunisolarOptions` and `DataLoaderStrategy` types.

## 2. Build Process for Static Bundling

The key challenge is making the JSON data available *before* Rollup runs. This requires adjusting the build scripts.

-   [ ] **Create a `prebuild` script (`scripts/copy-data-to-src.mjs`)**.
    -   This script will copy the JSON data from the root `output/json` directory to a new `pkg/src/data/precomputed` directory.
    -   This makes the data available for static `import()` statements.

-   [ ] **Create the Manifest Generation Script (`scripts/generate-data-manifest.mjs`)**.
    -   This script will scan `pkg/src/data/precomputed` and generate `pkg/src/data/manifest.ts`.
    -   The generated manifest will export a `loadData(dataType, year)` function containing `switch` statements that map to dynamic `import('./precomputed/.../{year}.json')` calls.

-   [ ] **Update `package.json` Scripts**.
    -   Add a new `prebuild` script that runs the two scripts above in order.
    -   Modify the `build` script to be: `npm run prebuild && rollup -c`.
    -   The existing `postbuild` script (`scripts/copy-data.mjs`) should remain, as it's needed to place the data in `dist/data` for the CDN/fetch strategy.

-   [ ] **Update `.gitignore`**.
    -   Add `src/data/precomputed/` to `pkg/.gitignore` to prevent the copied data from being committed to version control.

## 3. Data Loading Strategy Implementation

-   [ ] **Implement Strategy Switching in `DataLoader`**.
    -   The main data-fetching method (e.g., `getNewMoons`) will check the global config.
    -   If `strategy === 'static'`, it will call the function from the generated `src/data/manifest.ts`.
    -   If `strategy === 'fetch'` (the default), it will proceed with the fetch/fs logic.

-   [ ] **Enhance the 'Fetch' Strategy**.
    -   **Default to CDN**: If `baseUrl` is not provided, default to `https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/data`.
    -   **Inject Package Version**: Modify the build process (e.g., using `rollup-plugin-replace`) to inject the package version from `package.json` into the code to build the correct CDN URL automatically.
    -   **Retain `fs` Fallback**: Keep the existing `fs` logic as a final fallback for classic Node.js environments when a relative path is used.

## 4. Integration and Refactoring

-   [ ] **Update `LunisolarCalendar.ts`**.
    -   Remove the direct instantiation: `new DataLoader({ baseUrl: './data' })`.
    -   Instead, import a single, shared instance of the `DataLoader` and use it.

-   [ ] **Update `ConstructionStars.ts`**.
    -   The static method `getAuspiciousDays` also instantiates a `DataLoader`. Refactor it to use the shared instance.

## 5. Documentation and Testing

-   [ ] **Update `README.md` and `docs/serverless.md`**.
    -   Document the new `configure()` method and explain the `'fetch'` vs. `'static'` strategies with clear examples for Vercel, browsers, and Node.js.
-   [ ] **Update Unit/Integration Tests**.
    -   Modify tests in `tests/` to work with the new configuration system.
    -   Add tests specifically for the static bundling strategy.
    -   Add tests to verify the CDN fallback URL is constructed correctly.
    -   Ensure the `fs` fallback continues to work as expected.
