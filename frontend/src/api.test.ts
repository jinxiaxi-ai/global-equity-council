import { afterEach, describe, expect, it, vi } from "vitest";
import { searchAssets } from "./api";

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
});
