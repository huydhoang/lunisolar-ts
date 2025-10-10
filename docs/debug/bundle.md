As package maintainer: better way to ship precomputed data
Avoid fs at runtime in serverless. Provide a configurable, bundler- and edge-friendly data loading strategy:

Recommended design for lunisolar-ts
- Configurable data source (no fs by default)
  - Expose a top-level option (e.g., options.data.baseUrl) that is passed into your internal loader (no private-only control). Consumers can host the JSON under their public/ or a CDN and pass baseUrl (e.g., "/lunisolar-data" or "https://cdn.example.com/lunisolar").
  - Resolution order:
    - If baseUrl provided: fetch(`${baseUrl}/${kind}/${year}.json`)
    - Else if in a browser or fetch-capable environment: use unpkg/jsDelivr pinned to the current package version (immutable)
    - Else fallback safely to fs only in classic Node where a computed path exists
- Bundler-friendly static imports (optional mode for embedding)
  - Generate a manifest module at build time mapping years to static imports (or to dynamic import() with explicit paths) so bundlers can include JSON assets into SSR bundles.
  - Example strategy (described, not code): a new_moons_index module exports get(year) that switches on year and returns import("./new_moons/2024.json", { assert: { type: "json" }}). Because the import specifiers are static strings, bundlers include the assets; no fs resolution; tree-shakeable by year.
- Provide a CDN fallback
  - Document a default CDN base like: https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data
  - This makes serverless “just work” even without copying files.
- Keep data in package tarball
  - Ensure "files": ["dist", "dist/data", ...] in the package to ship the JSON.
  - Avoid runtime-generated paths that depend on project layout.
- Minimal public API adjustment
  - A top-level factory or configure method that accepts { timezone, data: { baseUrl?: string } } is enough for most frameworks (Astro/Vercel/Next) to pass a public path or CDN and avoid fs entirely.

Outcome
- With the changes in [astro.config.mjs](astro.config.mjs), [package.json](package.json), and [scripts/copy-lunisolar-data.mjs](scripts/copy-lunisolar-data.mjs), the current build will package the data where the runtime expects it, resolving the ENOENT.
- The library guidance above removes the need for file-copy workarounds for all serverless/bundled users going forward.