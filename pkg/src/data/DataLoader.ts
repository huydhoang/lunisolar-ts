import type { TNewMoon, TSolarTerm } from '../types';

export type DataLoaderOptions = {
  /** Base URL or path where the data directory is served from. Defaults to './data'. */
  baseUrl?: string;
};

/**
 * DataLoader lazily loads JSON chunks for a given year and caches them.
 *
 * Expected layout at runtime (Phase 6 will copy these files):
 *   dist/data/new_moons/{year}.json
 *   dist/data/solar_terms/{year}.json
 */
export class DataLoader {
  private _cache = new Map<string, unknown>();
  private _baseUrl: string;

  constructor(opts: DataLoaderOptions = {}) {
    this._baseUrl = opts.baseUrl ?? './data';
  }

  async getNewMoons(year: number): Promise<TNewMoon[]> {
    return this._get<number[]>(`new_moons:${year}`, this._url('new_moons', year));
  }

  async getSolarTerms(year: number): Promise<TSolarTerm[]> {
    return this._get<number[]>(`solar_terms:${year}`, this._url('solar_terms', year));
  }

  private _url(kind: 'new_moons' | 'solar_terms', year: number): string {
    return `${this._baseUrl}/${kind}/${year}.json`;
  }

  private async _get<T>(key: string, urlOrPath: string): Promise<T> {
    if (this._cache.has(key)) return this._cache.get(key) as T;
    const data = await this._loadJson<T>(urlOrPath);
    this._cache.set(key, data);
    return data;
  }

  private async _loadJson<T>(urlOrPath: string): Promise<T> {
    const looksLikeHttp = /^(https?:)?\/\//i.test(urlOrPath);
    const looksRelative = urlOrPath.startsWith('./') || urlOrPath.startsWith('../') || urlOrPath.startsWith('data/');

    // Prefer filesystem for relative paths in Node/test environments
    if ((looksRelative || !looksLikeHttp) && typeof process !== 'undefined' && process.versions?.node) {
      const [{ readFile }, { fileURLToPath }, { resolve, dirname }] = await Promise.all([
        import('node:fs/promises'),
        import('node:url'),
        import('node:path'),
      ]);
      const base = typeof import.meta !== 'undefined' ? dirname(fileURLToPath(import.meta.url)) : process.cwd();
      const filePath = resolve(base, urlOrPath);
      const txt = await readFile(filePath, 'utf-8');
      return JSON.parse(txt) as T;
    }

    // Otherwise attempt fetch (browser or fully-qualified URLs)
    if (typeof fetch === 'function') {
      const res = await fetch(urlOrPath);
      if (!res.ok) throw new Error(`Failed to load ${urlOrPath}: ${res.status} ${res.statusText}`);
      return (await res.json()) as T;
    }

    throw new Error('No supported method to load data in this environment.');
  }
}
