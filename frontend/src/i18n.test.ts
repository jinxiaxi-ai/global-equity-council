import { describe, expect, it } from "vitest";
import { useCopy } from "./i18n";

describe("bilingual copy", () => {
  it("provides matching critical interface labels", () => {
    const zh = useCopy("zh");
    const en = useCopy("en");
    expect(zh.searchLabel).toContain("搜索");
    expect(en.searchLabel).toContain("Search");
    expect(zh.share).not.toEqual(en.share);
    expect(zh.footer).toContain("不构成投资建议");
    expect(en.footer).toContain("Not investment advice");
  });
});
