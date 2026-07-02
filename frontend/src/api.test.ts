import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzeAsset, searchAssets } from "./api";

afterEach(() => vi.restoreAllMocks());

describe("API client", () => {
  it("encodes global security search input", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("[]", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await searchAssets("600519.SS");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/assets/search?q=600519.SS",
      expect.objectContaining({ signal: undefined }),
    );
  });

  it("surfaces API recovery detail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Fixture unavailable" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(searchAssets("UNKNOWN")).rejects.toThrow(
      "Fixture unavailable",
    );
  });

  it("sends browser-local BYOK settings only with analysis requests", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ report_id: "demo" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await analyzeAsset("XNAS:AAOI", "USD", "zh-CN", {
      provider: "twelvedata",
      apiKey: "user-key",
    });
    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(String(init?.body))).toMatchObject({
      asset_id: "XNAS:AAOI",
      market_data_provider: "twelvedata",
      market_data_api_key: "user-key",
    });
  });
});
