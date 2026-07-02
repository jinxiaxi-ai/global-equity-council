import type { AnalysisReport, SearchResult } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export type MarketDataProvider = "fixture" | "twelvedata" | "finnhub";

export type DataSourceConfig = {
  provider: MarketDataProvider;
  apiKey: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function searchAssets(
  query: string,
  signal?: AbortSignal,
): Promise<SearchResult[]> {
  return request<SearchResult[]>(
    `/assets/search?q=${encodeURIComponent(query)}`,
    { signal },
  );
}

export async function analyzeAsset(
  assetId: string,
  baseCurrency: string,
  locale: string,
  dataSource?: DataSourceConfig,
): Promise<AnalysisReport> {
  return request<AnalysisReport>("/analysis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      asset_id: assetId,
      base_currency: baseCurrency,
      locale,
      market_data_provider: dataSource?.provider,
      market_data_api_key:
        dataSource && dataSource.provider !== "fixture"
          ? dataSource.apiKey.trim()
          : undefined,
    }),
  });
}
