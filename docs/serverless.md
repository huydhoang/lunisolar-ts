# Bundling Precomputed Data for Serverless/Edge Environments

The `lunisolar-ts` package requires precomputed astronomical data to perform its calculations. In a standard Node.js environment, this data can be loaded from the filesystem at runtime using `fs`. However, serverless and edge computing environments (like Vercel Serverless Functions, AWS Lambda, or Cloudflare Workers) have a read-only filesystem and do not support Node's `fs` module for runtime file access.

This document outlines robust and performant strategies to bundle and load this precomputed data, ensuring the package works seamlessly in any environment.

## The Challenge: Filesystem Limitations

The core issue is that lazy-loading JSON files from the package directory via `fs.readFileSync` will fail in a serverless environment, resulting in `ENOENT` (No such file or directory) errors. The data must be made available to the code without relying on runtime filesystem reads.

## Recommended Approaches

The ideal solution is to offer multiple data-loading strategies that are configurable by the end-user, making the library adaptable and "just work" by default in most scenarios.

### 1. Dynamic Loading via Fetch (Default Strategy)

This approach replaces filesystem access with network requests using the `fetch` API, which is universally available in serverless/edge environments and browsers.

#### How It Works:

1.  **Configurable Base URL**: The library should expose a configuration option (e.g., `options.data.baseUrl`) allowing users to specify a URL from which to load the data files. Users can host the data themselves, for example, in their public assets folder (`/my-app-data`) or on a private CDN. The library would then fetch data from a path like `${baseUrl}/${dataType}/${year}.json`.

2.  **Default CDN Fallback**: If the `baseUrl` is not provided, the library should default to a reliable public CDN like jsDelivr or unpkg. It should be pinned to the specific version of the `lunisolar-ts` package to ensure data immutability and prevent unexpected breaking changes.
    - **Example URL**: `https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data`
    - This makes the library work out-of-the-box in serverless environments with zero configuration.

3.  **Legacy `fs` Fallback**: For backward compatibility in traditional Node.js environments where `fetch` might not be preferred or available, the library can fall back to using `fs` as a last resort.

This strategy keeps the user's application bundle small, as the data is loaded on demand.

### 2. Static Bundling via Imports (Embed Strategy)

This approach allows users to embed the required data directly into their application bundle at build time. This is the most performant option as it avoids runtime network latency.

#### How It Works:

1.  **Build-Time Manifest**: During the package's build process, generate a manifest module (e.g., `data-loader.js`). This module contains a function that maps a data type and year to a static import path.

2.  **Static `import()`**: The manifest uses dynamic `import()` expressions with **static string literals**. Modern bundlers (like Webpack, Rollup, Vite) can detect these paths, which tells them to include the corresponding JSON files in the final server bundle.

    ```javascript
    // Example generated data loader
    export function getData(dataType, year) {
      switch (dataType) {
        case 'new_moons':
          // The static path allows bundlers to find and include the file
          return import(`./new_moons/${year}.json`, { assert: { type: "json" }});
        // ... other cases
      }
    }
    ```

3.  **Tree-Shaking**: Because the imports are explicit, this approach is tree-shakeable. If a user's code only ever requests data for the year 2025, the bundler can be configured to exclude the data for all other years, leading to a highly optimized and minimal bundle.

This strategy is ideal for users who want maximum performance and predictability, and are comfortable with a larger initial bundle size.

## Summary of Strategies

| Strategy                 | Pros                                                              | Cons                                                              | Best For                                                              |
| ------------------------ | ----------------------------------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Dynamic Loading (Fetch)** | - Zero-config for serverless (CDN default)<br>- Small initial bundle size | - Runtime network latency<br>- Relies on external network availability | General-purpose use, especially in client-side or serverless contexts. |
| **Static Bundling (Import)** | - Zero network latency at runtime<br>- Data is co-located with code<br>- Tree-shakeable for minimal size | - Increases application bundle size<br>- Requires a bundler-aware setup | Performance-critical applications and server-side rendering (SSR).   |

By implementing a configurable system that supports both dynamic fetching and static bundling, `lunisolar-ts` can provide a robust, performant, and developer-friendly experience across all JavaScript environments.
